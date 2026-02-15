from flask import Blueprint, jsonify
from flask_migrate import upgrade
from app.extensions import db
import os

bp = Blueprint("migration", __name__)


@bp.route("/run", methods=["POST"])
def run_migration():
    """
    Temporary endpoint to run database migrations on Vercel.
    DELETE THIS ENDPOINT AFTER RUNNING THE MIGRATION!
    """
    try:
        # Get the migrations directory
        migrations_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "migrations"
        )

        # Run the migration
        upgrade(directory=migrations_dir)

        return jsonify({
            "success": True,
            "message": "Migration completed successfully"
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
