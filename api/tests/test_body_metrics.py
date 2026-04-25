from datetime import datetime, timezone

import pytest

from app.extensions import db as _db
from app.models.body_metric import BodyFatLog
from app.models.user import User, Profile, ProfessionalPatient
from tests.conftest import get_auth_header


def _verify_by_email(email):
    """Mark a user as email-verified so /auth/login succeeds (fetched in current session)."""
    user = User.query.filter_by(email=email).first()
    if user and not user.email_verified:
        user.email_verified = True
        _db.session.commit()


@pytest.fixture
def patient_headers(client, app, patient):
    with app.app_context():
        _verify_by_email("test_patient@bt.app")
    return get_auth_header(client, "test_patient@bt.app", "Patient123!")


@pytest.fixture
def professional_headers(client, app, professional):
    with app.app_context():
        _verify_by_email("test_pro@bt.app")
    return get_auth_header(client, "test_pro@bt.app", "Pro123!aa")


# ── Endpoints under test (one shape, five tables). ──
ENDPOINTS = [
    ("/api/v1/body-fat-logs", "body_fat_pct", 18.5, 1.0, 80.0),
    ("/api/v1/muscle-mass-logs", "muscle_mass_kg", 65.5, 1.0, 500.0),
    ("/api/v1/waist-measurements", "waist_cm", 82.0, 5.0, 500.0),
    ("/api/v1/hips-measurements", "hips_cm", 98.0, 5.0, 500.0),
    ("/api/v1/neck-measurements", "neck_cm", 38.0, 1.0, 500.0),
]


@pytest.mark.parametrize("url,field,valid,low,high", ENDPOINTS)
def test_create_entry_success(client, patient_headers, url, field, valid, low, high):
    resp = client.post(
        url,
        headers=patient_headers,
        json={field: valid, "recorded_at": "2026-04-25T10:00:00+00:00", "notes": "ok"},
    )
    assert resp.status_code == 201, resp.get_json()
    data = resp.get_json()["data"]
    assert data[field] == valid
    assert data["notes"] == "ok"


@pytest.mark.parametrize("url,field,valid,low,high", ENDPOINTS)
def test_create_below_range_rejected(client, patient_headers, url, field, valid, low, high):
    resp = client.post(
        url,
        headers=patient_headers,
        json={field: low, "recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    assert resp.status_code == 422


@pytest.mark.parametrize("url,field,valid,low,high", ENDPOINTS)
def test_create_above_range_rejected(client, patient_headers, url, field, valid, low, high):
    resp = client.post(
        url,
        headers=patient_headers,
        json={field: high, "recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    assert resp.status_code == 422


def test_create_missing_value_rejected(client, patient_headers):
    resp = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={"recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    assert resp.status_code == 422


def test_create_missing_date_rejected(client, patient_headers):
    resp = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={"body_fat_pct": 20.0},
    )
    assert resp.status_code == 422


def test_create_unauthenticated_rejected(client):
    resp = client.post(
        "/api/v1/body-fat-logs",
        json={"body_fat_pct": 20.0, "recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    assert resp.status_code == 401


def test_list_filters_to_own_data_only(client, app, patient, patient_headers):
    # Seed an entry belonging to a different patient — current user must NOT see it
    # (regardless of how many entries the test patient already has from other tests).
    with app.app_context():
        other = User.query.filter_by(email="other_patient@bt.app").first()
        if not other:
            other = User(
                email="other_patient@bt.app",
                first_name="Other",
                last_name="One",
                role="patient",
                email_verified=True,
            )
            other.set_password("Other1234!")
            _db.session.add(other)
            _db.session.flush()
            _db.session.add(Profile(user_id=other.id))
            _db.session.commit()
        other_id = str(other.id)
        _db.session.add(
            BodyFatLog(
                patient_id=other.id,
                body_fat_pct=22.0,
                recorded_at=datetime(2026, 4, 20, 10, 0, tzinfo=timezone.utc),
            )
        )
        _db.session.commit()
        my_id = str(patient.id)

    resp = client.get("/api/v1/body-fat-logs", headers=patient_headers)
    assert resp.status_code == 200
    items = resp.get_json()["data"]
    patient_ids = {item["patient_id"] for item in items}
    assert other_id not in patient_ids
    assert patient_ids <= {my_id}


def test_patient_cannot_create_for_other_patient(client, app, patient, patient_headers):
    with app.app_context():
        other = User.query.filter_by(email="other_patient@bt.app").first()
        if not other:
            other = User(
                email="other_patient@bt.app",
                first_name="Other",
                last_name="One",
                role="patient",
                email_verified=True,
            )
            other.set_password("Other1234!")
            _db.session.add(other)
            _db.session.flush()
            _db.session.add(Profile(user_id=other.id))
            _db.session.commit()
        other_id = str(other.id)

    # Patients always create for themselves; supplied patient_id is ignored.
    resp = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={
            "patient_id": other_id,
            "body_fat_pct": 19.0,
            "recorded_at": "2026-04-25T10:00:00+00:00",
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["patient_id"] != other_id


def test_unassigned_professional_forbidden(client, app, patient, professional_headers):
    # Professional is not assigned to the patient → 403 when targeting them explicitly.
    with app.app_context():
        patient_id = str(patient.id)
    resp = client.post(
        "/api/v1/body-fat-logs",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "body_fat_pct": 18.0,
            "recorded_at": "2026-04-25T10:00:00+00:00",
        },
    )
    assert resp.status_code == 403


def test_assigned_professional_can_create_for_patient(
    client, app, patient, professional, professional_headers
):
    with app.app_context():
        existing = ProfessionalPatient.query.filter_by(
            professional_id=professional.id, patient_id=patient.id
        ).first()
        if not existing:
            _db.session.add(
                ProfessionalPatient(
                    professional_id=professional.id, patient_id=patient.id, is_active=True
                )
            )
            _db.session.commit()
        patient_id = str(patient.id)

    resp = client.post(
        "/api/v1/body-fat-logs",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "body_fat_pct": 21.0,
            "recorded_at": "2026-04-25T10:00:00+00:00",
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["patient_id"] == patient_id


def test_me_includes_body_metrics_stats(client, patient_headers):
    # Use a far-future recorded_at so this entry wins the "latest" query
    # regardless of what earlier tests inserted into the shared in-memory DB.
    client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={"body_fat_pct": 25.5, "recorded_at": "2099-12-31T10:00:00+00:00"},
    )
    resp = client.get("/api/v1/auth/me", headers=patient_headers)
    user = resp.get_json()["user"]
    stats = user.get("body_metrics_stats")
    assert stats is not None
    assert set(stats.keys()) == {
        "body_fat_pct", "muscle_mass_kg", "waist_cm", "hips_cm", "neck_cm",
    }
    assert stats["body_fat_pct"]["value"] == 25.5


def test_update_value_with_validation(client, patient_headers):
    create = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={"body_fat_pct": 20.0, "recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    entry_id = create.get_json()["data"]["id"]

    # In-range update succeeds.
    ok = client.patch(
        f"/api/v1/body-fat-logs/{entry_id}",
        headers=patient_headers,
        json={"body_fat_pct": 22.5},
    )
    assert ok.status_code == 200
    assert ok.get_json()["data"]["body_fat_pct"] == 22.5

    # Out-of-range update is rejected.
    bad = client.patch(
        f"/api/v1/body-fat-logs/{entry_id}",
        headers=patient_headers,
        json={"body_fat_pct": 200.0},
    )
    assert bad.status_code == 422


def test_create_rejects_nan(client, patient_headers):
    resp = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={"body_fat_pct": float("nan"), "recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    assert resp.status_code == 422


def test_create_rejects_infinity(client, patient_headers):
    resp = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={"body_fat_pct": float("inf"), "recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    assert resp.status_code == 422


def test_create_rejects_oversized_notes(client, patient_headers):
    resp = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={
            "body_fat_pct": 20.0,
            "recorded_at": "2026-04-25T10:00:00+00:00",
            "notes": "x" * 1001,
        },
    )
    assert resp.status_code == 422


def test_patch_rejects_invalid_recorded_at(client, patient_headers):
    create = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={"body_fat_pct": 20.0, "recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    entry_id = create.get_json()["data"]["id"]
    bad = client.patch(
        f"/api/v1/body-fat-logs/{entry_id}",
        headers=patient_headers,
        json={"recorded_at": "not-a-date"},
    )
    assert bad.status_code == 422


def test_delete_entry(client, patient_headers):
    create = client.post(
        "/api/v1/body-fat-logs",
        headers=patient_headers,
        json={"body_fat_pct": 20.0, "recorded_at": "2026-04-25T10:00:00+00:00"},
    )
    entry_id = create.get_json()["data"]["id"]
    resp = client.delete(f"/api/v1/body-fat-logs/{entry_id}", headers=patient_headers)
    assert resp.status_code == 200
    follow = client.get(f"/api/v1/body-fat-logs/{entry_id}", headers=patient_headers)
    assert follow.status_code == 404
