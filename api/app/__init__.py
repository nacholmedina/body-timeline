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
    allowed_origins = [o.strip() for o in app.config["FRONTEND_URL"].split(",")]
    # Also accept Vercel preview deployment URLs
    if any("vercel.app" in o for o in allowed_origins):
        allowed_origins.append(r"https://.*\.vercel\.app")
    cors.init_app(app, resources={r"/api/*": {"origins": allowed_origins}})

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

    @app.route("/api/debug/storage")
    def debug_storage():
        """Temporary debug endpoint — remove after confirming storage works."""
        cfg = app.config
        info = {
            "backend": cfg.get("STORAGE_BACKEND"),
            "s3_bucket": cfg.get("S3_BUCKET"),
            "s3_endpoint": cfg.get("S3_ENDPOINT_URL", "")[:50] + "..." if cfg.get("S3_ENDPOINT_URL") else "",
            "s3_region": cfg.get("S3_REGION"),
            "s3_key_set": bool(cfg.get("S3_ACCESS_KEY")),
            "s3_secret_set": bool(cfg.get("S3_SECRET_KEY")),
        }
        try:
            from app.services.storage import get_storage
            storage = get_storage()
            info["storage_class"] = type(storage).__name__
            info["boto3_ok"] = True
        except Exception as e:
            info["storage_error"] = f"{type(e).__name__}: {e}"
            info["boto3_ok"] = False
        return info

    return app
