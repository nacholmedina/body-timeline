from flask import Blueprint, jsonify
from app.extensions import db

bp = Blueprint("migration", __name__)


@bp.route("/run", methods=["POST"])
def run_migration():
    """
    Temporary endpoint to create exercise tables and seed data on Vercel.
    DELETE THIS ENDPOINT AFTER RUNNING THE MIGRATION!
    """
    try:
        # Drop old workout-related tables
        db.session.execute(db.text("DROP TABLE IF EXISTS workout_photos CASCADE"))
        db.session.execute(db.text("DROP TABLE IF EXISTS workout_items CASCADE"))
        db.session.execute(db.text("DROP TABLE IF EXISTS workouts CASCADE"))
        db.session.execute(db.text("DROP TABLE IF EXISTS exercises CASCADE"))
        db.session.commit()

        # Create enum types if they don't exist
        db.session.execute(db.text("""
            DO $$ BEGIN
                CREATE TYPE exercise_category AS ENUM ('cardio', 'strength', 'sports', 'flexibility', 'general');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))

        db.session.execute(db.text("""
            DO $$ BEGIN
                CREATE TYPE exercise_request_status AS ENUM ('pending', 'approved', 'rejected');
            EXCEPTION
                WHEN duplicate_object THEN null;
            END $$;
        """))
        db.session.commit()

        # Create exercise_definitions table
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS exercise_definitions (
                id VARCHAR(36) NOT NULL,
                name VARCHAR(200) NOT NULL,
                category exercise_category NOT NULL,
                description TEXT,
                allowed_measurements TEXT,
                is_system BOOLEAN NOT NULL DEFAULT FALSE,
                is_active BOOLEAN NOT NULL DEFAULT TRUE,
                usage_count INTEGER NOT NULL DEFAULT 0,
                created_by VARCHAR(36),
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(created_by) REFERENCES users (id),
                UNIQUE (name)
            )
        """))

        # Create indexes
        db.session.execute(db.text("""
            CREATE INDEX IF NOT EXISTS ix_exercise_definitions_name
            ON exercise_definitions (name)
        """))
        db.session.execute(db.text("""
            CREATE INDEX IF NOT EXISTS ix_exercise_definitions_category
            ON exercise_definitions (category)
        """))
        db.session.execute(db.text("""
            CREATE INDEX IF NOT EXISTS ix_exercise_defs_category_usage
            ON exercise_definitions (category, is_active, usage_count)
        """))

        # Create exercise_logs table
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS exercise_logs (
                id VARCHAR(36) NOT NULL,
                user_id VARCHAR(36) NOT NULL,
                exercise_definition_id VARCHAR(36),
                custom_exercise_name VARCHAR(200),
                custom_exercise_description TEXT,
                measurements TEXT,
                performed_at TIMESTAMP WITH TIME ZONE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY(exercise_definition_id) REFERENCES exercise_definitions (id)
            )
        """))

        # Create indexes for exercise_logs
        db.session.execute(db.text("""
            CREATE INDEX IF NOT EXISTS ix_exercise_logs_user_id
            ON exercise_logs (user_id)
        """))
        db.session.execute(db.text("""
            CREATE INDEX IF NOT EXISTS ix_exercise_logs_user_performed
            ON exercise_logs (user_id, performed_at DESC)
        """))

        # Create exercise_photos table
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS exercise_photos (
                id VARCHAR(36) NOT NULL,
                exercise_log_id VARCHAR(36) NOT NULL,
                photo_url VARCHAR(500) NOT NULL,
                display_order INTEGER NOT NULL DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(exercise_log_id) REFERENCES exercise_logs (id) ON DELETE CASCADE
            )
        """))

        # Create exercise_requests table
        db.session.execute(db.text("""
            CREATE TABLE IF NOT EXISTS exercise_requests (
                id VARCHAR(36) NOT NULL,
                requested_by VARCHAR(36) NOT NULL,
                exercise_name VARCHAR(200) NOT NULL,
                category exercise_category NOT NULL,
                description TEXT,
                suggested_measurements TEXT,
                status exercise_request_status NOT NULL,
                admin_notes TEXT,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
                PRIMARY KEY (id),
                FOREIGN KEY(requested_by) REFERENCES users (id) ON DELETE CASCADE
            )
        """))

        db.session.commit()

        # Seed the exercise catalog
        from app.services.exercise_seed import seed_exercise_catalog
        exercise_count = seed_exercise_catalog()

        return jsonify({
            "success": True,
            "message": f"Migration completed successfully. Created {exercise_count} system exercises."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
