from app.routes.auth import bp as auth_bp
from app.routes.meals import bp as meals_bp
from app.routes.weigh_ins import bp as weigh_ins_bp
from app.routes.goals import bp as goals_bp
# Old routes - commented out to avoid model conflicts
# from app.routes.exercises import bp as exercises_bp
# from app.routes.workouts import bp as workouts_bp
from app.routes.notifications import bp as notifications_bp
from app.routes.appointments import bp as appointments_bp
from app.routes.dashboard import bp as dashboard_bp
from app.routes.admin import bp as admin_bp
from app.routes.professional import bp as professional_bp
from app.routes.invitations import bp as invitations_bp
from app.routes.meal_comments import bp as meal_comments_bp

# New exercise tracking routes
from app.routes.exercise_definitions import bp as exercise_definitions_bp
from app.routes.exercise_logs import bp as exercise_logs_bp
from app.routes.exercise_requests_new import bp as exercise_requests_new_bp


def register_blueprints(app):
    prefix = "/api/v1"
    app.register_blueprint(auth_bp, url_prefix=f"{prefix}/auth")
    app.register_blueprint(meals_bp, url_prefix=f"{prefix}/meals")
    app.register_blueprint(weigh_ins_bp, url_prefix=f"{prefix}/weigh-ins")
    app.register_blueprint(goals_bp, url_prefix=f"{prefix}/goals")
    # Old routes - commented out
    # app.register_blueprint(exercises_bp, url_prefix=f"{prefix}/exercises")
    # app.register_blueprint(workouts_bp, url_prefix=f"{prefix}/workouts")
    app.register_blueprint(notifications_bp, url_prefix=f"{prefix}/notifications")
    app.register_blueprint(appointments_bp, url_prefix=f"{prefix}/appointments")
    app.register_blueprint(dashboard_bp, url_prefix=f"{prefix}/dashboard")
    app.register_blueprint(admin_bp, url_prefix=f"{prefix}/admin")
    app.register_blueprint(professional_bp, url_prefix=f"{prefix}/professional")
    app.register_blueprint(invitations_bp, url_prefix=f"{prefix}/invitations")
    app.register_blueprint(meal_comments_bp, url_prefix=f"{prefix}/meal-comments")

    # New exercise tracking routes
    app.register_blueprint(exercise_definitions_bp, url_prefix=f"{prefix}/exercise-definitions")
    app.register_blueprint(exercise_logs_bp, url_prefix=f"{prefix}/exercise-logs")
    app.register_blueprint(exercise_requests_new_bp, url_prefix=f"{prefix}/exercise-requests")
