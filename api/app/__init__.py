import os
import uuid as _uuid

from flask import Flask, send_from_directory

from app.config import Config
from app.extensions import db, jwt, cors, migrate
from app.utils.errors import register_error_handlers
from app.services.storage import reset_storage


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_override:
        app.config.update(config_override)

    # Extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["FRONTEND_URL"].split(",")}})

    # Reset storage on new app context
    with app.app_context():
        reset_storage()

    # Error handlers
    register_error_handlers(app)

    # JWT user loader
    from app.models.user import User

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        if isinstance(user, User):
            return str(user.id)
        return str(user)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        return db.session.get(User, _uuid.UUID(identity))

    # Register blueprints
    from app.routes import register_blueprints
    register_blueprints(app)

    # Serve uploaded files in development
    uploads_dir = os.path.join(app.root_path, "..", app.config.get("STORAGE_LOCAL_PATH", "uploads"))

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        return send_from_directory(os.path.abspath(uploads_dir), filename)

    @app.route("/api/health")
    def health():
        return {"status": "ok", "app": "Body Timeline"}

    return app
