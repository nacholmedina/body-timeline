import pytest
from tests.conftest import get_auth_header
from app.extensions import db
from app.models.user import ProfessionalPatient


def test_devadmin_can_create_exercise(client, devadmin):
    headers = get_auth_header(client, "test_admin@bt.app", "Admin123!")
    resp = client.post("/api/v1/exercises", json={
        "name": "Bench Press", "exercise_type": "sets_reps", "muscle_group": "chest",
    }, headers=headers)
    assert resp.status_code == 201


def test_patient_cannot_create_exercise(client, patient):
    headers = get_auth_header(client, "test_patient@bt.app", "Patient123!")
    resp = client.post("/api/v1/exercises", json={
        "name": "Squat", "exercise_type": "sets_reps",
    }, headers=headers)
    assert resp.status_code == 403


def test_professional_cannot_create_exercise(client, professional):
    headers = get_auth_header(client, "test_pro@bt.app", "Pro123!aa")
    resp = client.post("/api/v1/exercises", json={
        "name": "Deadlift", "exercise_type": "sets_reps",
    }, headers=headers)
    assert resp.status_code == 403


def test_patient_can_create_own_meal(client, patient):
    headers = get_auth_header(client, "test_patient@bt.app", "Patient123!")
    resp = client.post("/api/v1/meals", json={
        "description": "Chicken salad",
        "eaten_at": "2026-01-15T12:00:00+00:00",
    }, headers=headers)
    assert resp.status_code == 201
    assert resp.get_json()["data"]["patient_id"] == str(patient.id)


def test_professional_cannot_create_meal(client, professional):
    headers = get_auth_header(client, "test_pro@bt.app", "Pro123!aa")
    resp = client.post("/api/v1/meals", json={
        "description": "Unauthorized meal",
        "eaten_at": "2026-01-15T12:00:00+00:00",
        "patient_id": "00000000-0000-0000-0000-000000000000",
    }, headers=headers)
    assert resp.status_code == 403


def test_patient_can_create_own_goal(client, patient):
    headers = get_auth_header(client, "test_patient@bt.app", "Patient123!")
    resp = client.post("/api/v1/goals", json={
        "title": "Run 5km", "period": "weekly",
    }, headers=headers)
    assert resp.status_code == 201


def test_patient_can_create_weigh_in(client, patient):
    headers = get_auth_header(client, "test_patient@bt.app", "Patient123!")
    resp = client.post("/api/v1/weigh-ins", json={
        "weight_kg": 75.5,
        "recorded_at": "2026-01-15T08:00:00+00:00",
    }, headers=headers)
    assert resp.status_code == 201


def test_professional_can_access_assigned_patient_weighins(client, app, professional, patient):
    with app.app_context():
        # Create assignment
        existing = ProfessionalPatient.query.filter_by(
            professional_id=professional.id, patient_id=patient.id
        ).first()
        if not existing:
            assignment = ProfessionalPatient(
                professional_id=professional.id, patient_id=patient.id
            )
            db.session.add(assignment)
            db.session.commit()

    headers = get_auth_header(client, "test_pro@bt.app", "Pro123!aa")
    resp = client.get(
        f"/api/v1/weigh-ins?patient_id={patient.id}", headers=headers
    )
    assert resp.status_code == 200


def test_devadmin_can_list_all_users(client, devadmin):
    headers = get_auth_header(client, "test_admin@bt.app", "Admin123!")
    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 200


def test_patient_cannot_list_users(client, patient):
    headers = get_auth_header(client, "test_patient@bt.app", "Patient123!")
    resp = client.get("/api/v1/admin/users", headers=headers)
    assert resp.status_code == 403


def test_only_patients_can_mark_notification_read(client, professional):
    headers = get_auth_header(client, "test_pro@bt.app", "Pro123!aa")
    resp = client.post(
        "/api/v1/notifications/00000000-0000-0000-0000-000000000000/read",
        headers=headers,
    )
    assert resp.status_code == 403
