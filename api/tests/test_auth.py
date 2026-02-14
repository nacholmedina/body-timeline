import pytest
from tests.conftest import get_auth_header


def test_register_success(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com",
        "password": "Test1234!",
        "first_name": "New",
        "last_name": "User",
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "newuser@test.com"
    assert data["user"]["role"] == "patient"


def test_register_duplicate_email(client):
    client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "password": "Test1234!",
        "first_name": "Dup", "last_name": "User",
    })
    resp = client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "password": "Test1234!",
        "first_name": "Dup", "last_name": "User",
    })
    assert resp.status_code == 409


def test_register_weak_password(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "weak@test.com", "password": "short",
        "first_name": "Weak", "last_name": "User",
    })
    assert resp.status_code == 422


def test_login_success(client, patient):
    resp = client.post("/api/v1/auth/login", json={
        "email": "test_patient@bt.app", "password": "Patient123!",
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data
    assert data["user"]["role"] == "patient"


def test_login_wrong_password(client, patient):
    resp = client.post("/api/v1/auth/login", json={
        "email": "test_patient@bt.app", "password": "wrong",
    })
    assert resp.status_code == 401


def test_me_authenticated(client, patient):
    headers = get_auth_header(client, "test_patient@bt.app", "Patient123!")
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "test_patient@bt.app"


def test_me_unauthenticated(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_refresh_token(client, patient):
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "test_patient@bt.app", "password": "Patient123!",
    })
    refresh_token = login_resp.get_json()["refresh_token"]

    resp = client.post("/api/v1/auth/refresh", headers={
        "Authorization": f"Bearer {refresh_token}",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()
