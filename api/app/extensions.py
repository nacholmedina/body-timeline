import uuid as _uuid

from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import types


class GUID(types.TypeDecorator):
    """Platform-independent UUID type that works with both PostgreSQL and SQLite."""
    impl = types.String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if not isinstance(value, _uuid.UUID):
                return _uuid.UUID(value)
        return value


db = SQLAlchemy()
jwt = JWTManager()
cors = CORS()
migrate = Migrate()
