import pytest

from app import create_app
from app.extensions import db as _db
from app.models.user import User, Profile


@pytest.fixture(scope="session")
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "JWT_SECRET_KEY": "test-secret",
        "STORAGE_BACKEND": "local",
        "STORAGE_LOCAL_PATH": "/tmp/bt-test-uploads",
        "FRONTEND_URL": "http://localhost:5173",
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def devadmin(app):
    with app.app_context():
        user = User.query.filter_by(email="test_admin@bt.app").first()
        if not user:
            user = User(email="test_admin@bt.app", first_name="Admin", last_name="Test", role="devadmin")
            user.set_password("Admin123!")
            _db.session.add(user)
            _db.session.flush()
            _db.session.add(Profile(user_id=user.id))
            _db.session.commit()
        return user


@pytest.fixture
def professional(app):
    with app.app_context():
        user = User.query.filter_by(email="test_pro@bt.app").first()
        if not user:
            user = User(email="test_pro@bt.app", first_name="Pro", last_name="Test", role="professional")
            user.set_password("Pro123!aa")
            _db.session.add(user)
            _db.session.flush()
            _db.session.add(Profile(user_id=user.id))
            _db.session.commit()
        return user


@pytest.fixture
def patient(app):
    with app.app_context():
        user = User.query.filter_by(email="test_patient@bt.app").first()
        if not user:
            user = User(email="test_patient@bt.app", first_name="Patient", last_name="Test", role="patient")
            user.set_password("Patient123!")
            _db.session.add(user)
            _db.session.flush()
            _db.session.add(Profile(user_id=user.id))
            _db.session.commit()
        return user


def get_auth_header(client, email, password):
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = resp.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
