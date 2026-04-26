"""Tests for bulk body-metric handling on weigh-in POST/PATCH/GET.

The bulk contract: callers send a `body_metrics` dict alongside the weigh-in
fields. For each metric column, a number means "upsert this value" and `null`
means "delete the linked entry, if any". Omitted keys are left alone (but
entries follow the weigh-in if `recorded_at` changes). The whole thing happens
in one DB transaction — a single bad metric value rolls everything back.
"""
from datetime import datetime, timezone

import pytest

from app.extensions import db as _db
from app.models.body_metric import (
    BodyFatLog,
    HipsMeasurement,
    MuscleMassLog,
    NeckMeasurement,
    WaistMeasurement,
)
from app.models.user import User, Profile, ProfessionalPatient
from app.models.weigh_in import WeighIn
from tests.conftest import get_auth_header


def _verify_by_email(email):
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


def _all_metrics(body_fat=18.5, muscle=65.0, waist=82.0, hips=98.0, neck=38.0):
    return {
        "body_fat_pct": body_fat,
        "muscle_mass_kg": muscle,
        "waist_cm": waist,
        "hips_cm": hips,
        "neck_cm": neck,
    }


def _new_recorded_at():
    """Return a unique ISO timestamp so tests don't collide on (patient_id, recorded_at)."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "+00:00")


# ── Create ───────────────────────────────────────────────────────────────────

def test_post_without_body_metrics_succeeds(client, patient_headers):
    """Creating a weigh-in without body_metrics still works (back-compat)."""
    resp = client.post(
        "/api/v1/weigh-ins",
        headers=patient_headers,
        json={"weight_kg": 80.0, "recorded_at": "2099-01-01T10:00:00+00:00"},
    )
    assert resp.status_code == 201
    data = resp.get_json()["data"]
    assert data["weight_kg"] == 80.0
    # New endpoint always echoes body_metrics, all None when nothing was sent
    assert data["body_metrics"] == {
        "body_fat_pct": None,
        "muscle_mass_kg": None,
        "waist_cm": None,
        "hips_cm": None,
        "neck_cm": None,
    }


def test_post_with_all_five_metrics_creates_rows(client, app, patient, patient_headers):
    """Single POST with all 5 metrics inserts a weigh-in + 5 body-metric rows."""
    recorded_at = "2099-02-01T10:00:00+00:00"
    resp = client.post(
        "/api/v1/weigh-ins",
        headers=patient_headers,
        json={
            "weight_kg": 75.5,
            "recorded_at": recorded_at,
            "body_metrics": _all_metrics(),
        },
    )
    assert resp.status_code == 201, resp.get_json()
    body = resp.get_json()["data"]["body_metrics"]
    assert body["body_fat_pct"]["body_fat_pct"] == 18.5
    assert body["muscle_mass_kg"]["muscle_mass_kg"] == 65.0
    assert body["waist_cm"]["waist_cm"] == 82.0
    assert body["hips_cm"]["hips_cm"] == 98.0
    assert body["neck_cm"]["neck_cm"] == 38.0

    # Server-side: all 5 rows exist and share patient_id + recorded_at with the weigh-in.
    with app.app_context():
        wi_id = resp.get_json()["data"]["id"]
        wi = _db.session.get(WeighIn, wi_id)
        for model, field, expected in [
            (BodyFatLog, "body_fat_pct", 18.5),
            (MuscleMassLog, "muscle_mass_kg", 65.0),
            (WaistMeasurement, "waist_cm", 82.0),
            (HipsMeasurement, "hips_cm", 98.0),
            (NeckMeasurement, "neck_cm", 38.0),
        ]:
            row = model.query.filter_by(patient_id=wi.patient_id, recorded_at=wi.recorded_at).one()
            assert float(getattr(row, field)) == expected


def test_post_with_partial_metrics_only_creates_filled_rows(client, app, patient_headers):
    """Mix of value + null in body_metrics: only filled keys get rows."""
    resp = client.post(
        "/api/v1/weigh-ins",
        headers=patient_headers,
        json={
            "weight_kg": 78.0,
            "recorded_at": "2099-03-01T10:00:00+00:00",
            "body_metrics": {
                "body_fat_pct": 20.0,
                "muscle_mass_kg": None,
                "waist_cm": 80.0,
                "hips_cm": None,
                "neck_cm": None,
            },
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()["data"]["body_metrics"]
    assert body["body_fat_pct"] is not None
    assert body["muscle_mass_kg"] is None
    assert body["waist_cm"] is not None
    assert body["hips_cm"] is None
    assert body["neck_cm"] is None


def test_post_invalid_metric_rolls_back_entire_transaction(client, app, patient, patient_headers):
    """One bad metric value → no weigh-in row is committed, no metric rows either."""
    with app.app_context():
        before_wi = WeighIn.query.filter_by(patient_id=patient.id).count()
        before_bf = BodyFatLog.query.filter_by(patient_id=patient.id).count()

    resp = client.post(
        "/api/v1/weigh-ins",
        headers=patient_headers,
        json={
            "weight_kg": 75.0,
            "recorded_at": "2099-04-01T10:00:00+00:00",
            "body_metrics": {
                "body_fat_pct": 18.0,
                "muscle_mass_kg": 65.0,
                "waist_cm": 9999.0,  # out of range → triggers rollback
                "hips_cm": None,
                "neck_cm": None,
            },
        },
    )
    assert resp.status_code == 422

    with app.app_context():
        after_wi = WeighIn.query.filter_by(patient_id=patient.id).count()
        after_bf = BodyFatLog.query.filter_by(patient_id=patient.id).count()
    assert after_wi == before_wi, "weigh-in should not be committed when a metric fails"
    assert after_bf == before_bf, "body-fat row should not be committed either"


# ── Update ───────────────────────────────────────────────────────────────────

def _create_baseline(client, patient_headers, recorded_at, body=None):
    resp = client.post(
        "/api/v1/weigh-ins",
        headers=patient_headers,
        json={"weight_kg": 70.0, "recorded_at": recorded_at, "body_metrics": body or {}},
    )
    assert resp.status_code == 201
    return resp.get_json()["data"]


def test_patch_without_body_metrics_leaves_metrics_alone(client, app, patient, patient_headers):
    recorded_at = "2099-05-01T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, recorded_at, body=_all_metrics())

    resp = client.patch(
        f"/api/v1/weigh-ins/{wi['id']}",
        headers=patient_headers,
        json={"weight_kg": 71.5},
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["weight_kg"] == 71.5
    body = resp.get_json()["data"]["body_metrics"]
    # Metrics still present and unchanged
    assert body["body_fat_pct"]["body_fat_pct"] == 18.5
    assert body["muscle_mass_kg"]["muscle_mass_kg"] == 65.0


def test_patch_adds_metric_that_didnt_exist(client, patient_headers):
    recorded_at = "2099-06-01T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, recorded_at)  # no metrics initially

    resp = client.patch(
        f"/api/v1/weigh-ins/{wi['id']}",
        headers=patient_headers,
        json={"body_metrics": {"body_fat_pct": 22.0}},
    )
    assert resp.status_code == 200
    body = resp.get_json()["data"]["body_metrics"]
    assert body["body_fat_pct"]["body_fat_pct"] == 22.0
    assert body["muscle_mass_kg"] is None  # untouched key stays absent


def test_patch_updates_existing_metric_value(client, patient_headers):
    recorded_at = "2099-07-01T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, recorded_at, body={"body_fat_pct": 20.0})

    resp = client.patch(
        f"/api/v1/weigh-ins/{wi['id']}",
        headers=patient_headers,
        json={"body_metrics": {"body_fat_pct": 25.5}},
    )
    assert resp.status_code == 200
    body = resp.get_json()["data"]["body_metrics"]
    assert body["body_fat_pct"]["body_fat_pct"] == 25.5


def test_patch_null_deletes_existing_metric(client, app, patient, patient_headers):
    recorded_at = "2099-08-01T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, recorded_at, body={"body_fat_pct": 20.0})

    resp = client.patch(
        f"/api/v1/weigh-ins/{wi['id']}",
        headers=patient_headers,
        json={"body_metrics": {"body_fat_pct": None}},
    )
    assert resp.status_code == 200
    assert resp.get_json()["data"]["body_metrics"]["body_fat_pct"] is None

    # Scoped by recorded_at: tests share the in-memory DB, so other tests'
    # body_fat_logs are present too — only check the row this test created.
    with app.app_context():
        wi_recorded = datetime.fromisoformat(recorded_at)
        assert (
            BodyFatLog.query.filter_by(
                patient_id=patient.id, recorded_at=wi_recorded
            ).count()
            == 0
        )


def test_patch_recorded_at_change_drags_metric_entries_along(
    client, app, patient, patient_headers
):
    """Changing the weigh-in's recorded_at should keep linked metric entries linked."""
    old_at = "2099-09-01T10:00:00+00:00"
    new_at = "2099-09-15T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, old_at, body={"body_fat_pct": 18.0})

    resp = client.patch(
        f"/api/v1/weigh-ins/{wi['id']}",
        headers=patient_headers,
        json={"recorded_at": new_at, "body_metrics": {"body_fat_pct": 18.0}},
    )
    assert resp.status_code == 200
    body = resp.get_json()["data"]["body_metrics"]
    assert body["body_fat_pct"]["recorded_at"].startswith("2099-09-15")

    with app.app_context():
        # Exactly one row, now living at the new recorded_at.
        rows = BodyFatLog.query.filter_by(patient_id=patient.id).all()
        rows = [r for r in rows if r.recorded_at.year == 2099 and r.recorded_at.month == 9]
        assert len(rows) == 1
        assert rows[0].recorded_at.day == 15


def test_patch_recorded_at_change_without_body_metrics_still_drags_links(
    client, app, patient, patient_headers
):
    """Even without a body_metrics field, linked entries follow recorded_at moves."""
    old_at = "2099-10-01T10:00:00+00:00"
    new_at = "2099-10-15T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, old_at, body={"waist_cm": 80.5})

    resp = client.patch(
        f"/api/v1/weigh-ins/{wi['id']}",
        headers=patient_headers,
        json={"recorded_at": new_at},
    )
    assert resp.status_code == 200
    body = resp.get_json()["data"]["body_metrics"]
    assert body["waist_cm"] is not None
    assert body["waist_cm"]["recorded_at"].startswith("2099-10-15")
    assert float(body["waist_cm"]["waist_cm"]) == 80.5

    # Old recorded_at slot must be empty for THIS row's value (tests share DB).
    with app.app_context():
        wi_old = datetime.fromisoformat(old_at)
        leftover = (
            WaistMeasurement.query.filter_by(patient_id=patient.id, recorded_at=wi_old)
            .filter(WaistMeasurement.waist_cm == 80.5)
            .count()
        )
        assert leftover == 0


def test_patch_invalid_metric_rolls_back_weighin_changes(
    client, app, patient, patient_headers
):
    """A bad metric value must not partially-apply weight or other metric changes."""
    recorded_at = "2099-11-01T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, recorded_at, body={"body_fat_pct": 18.0})

    resp = client.patch(
        f"/api/v1/weigh-ins/{wi['id']}",
        headers=patient_headers,
        json={
            "weight_kg": 99.0,
            "body_metrics": {
                "body_fat_pct": 25.0,        # would-be valid update
                "muscle_mass_kg": 9999.0,    # invalid → triggers rollback
            },
        },
    )
    assert resp.status_code == 422

    with app.app_context():
        wi_db = _db.session.get(WeighIn, wi["id"])
        assert float(wi_db.weight_kg) == 70.0, "weight should not have changed"
        # Scope to this weigh-in's recorded_at; the test DB carries other rows.
        wi_recorded = datetime.fromisoformat(recorded_at)
        bf = BodyFatLog.query.filter_by(
            patient_id=patient.id, recorded_at=wi_recorded
        ).one()
        assert float(bf.body_fat_pct) == 18.0, "body-fat should not have changed"
        assert (
            MuscleMassLog.query.filter_by(
                patient_id=patient.id, recorded_at=wi_recorded
            ).count()
            == 0
        )


# ── GET embedding ────────────────────────────────────────────────────────────

def test_get_with_include_returns_body_metrics(client, patient_headers):
    recorded_at = "2099-12-01T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, recorded_at, body={"body_fat_pct": 21.0})

    resp = client.get(
        f"/api/v1/weigh-ins/{wi['id']}?include=body_metrics", headers=patient_headers
    )
    assert resp.status_code == 200
    assert "body_metrics" in resp.get_json()["data"]
    assert resp.get_json()["data"]["body_metrics"]["body_fat_pct"]["body_fat_pct"] == 21.0


def test_get_without_include_omits_body_metrics(client, patient_headers):
    recorded_at = "2099-12-15T10:00:00+00:00"
    wi = _create_baseline(client, patient_headers, recorded_at, body={"body_fat_pct": 21.0})

    resp = client.get(f"/api/v1/weigh-ins/{wi['id']}", headers=patient_headers)
    assert resp.status_code == 200
    assert "body_metrics" not in resp.get_json()["data"]


# ── RBAC ─────────────────────────────────────────────────────────────────────

def test_unassigned_professional_cannot_bulk_create(client, app, patient):
    # Use a fresh professional with NO assignment history — the shared `professional`
    # fixture is reused across test files and may already be assigned to the patient
    # from earlier runs in the in-memory DB.
    with app.app_context():
        fresh = User.query.filter_by(email="fresh_pro@bt.app").first()
        if not fresh:
            fresh = User(
                email="fresh_pro@bt.app",
                first_name="Fresh",
                last_name="Pro",
                role="professional",
                email_verified=True,
            )
            fresh.set_password("Fresh123!aa")
            _db.session.add(fresh)
            _db.session.flush()
            _db.session.add(Profile(user_id=fresh.id))
            _db.session.commit()
        patient_id = str(patient.id)

    headers = get_auth_header(client, "fresh_pro@bt.app", "Fresh123!aa")
    resp = client.post(
        "/api/v1/weigh-ins",
        headers=headers,
        json={
            "patient_id": patient_id,
            "weight_kg": 70.0,
            "recorded_at": "2098-01-01T10:00:00+00:00",
            "body_metrics": _all_metrics(),
        },
    )
    assert resp.status_code == 403


def test_assigned_professional_can_bulk_create(
    client, app, patient, professional, professional_headers
):
    # Re-query users inside the active context to avoid DetachedInstanceError
    # when the fixture-bound session has been closed by an earlier test.
    with app.app_context():
        pro = User.query.filter_by(email="test_pro@bt.app").one()
        pat = User.query.filter_by(email="test_patient@bt.app").one()
        existing = ProfessionalPatient.query.filter_by(
            professional_id=pro.id, patient_id=pat.id
        ).first()
        if not existing:
            _db.session.add(
                ProfessionalPatient(
                    professional_id=pro.id, patient_id=pat.id, is_active=True
                )
            )
            _db.session.commit()
        elif not existing.is_active:
            existing.is_active = True
            _db.session.commit()
        patient_id = str(pat.id)

    resp = client.post(
        "/api/v1/weigh-ins",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "weight_kg": 72.0,
            "recorded_at": "2098-02-01T10:00:00+00:00",
            "body_metrics": {"body_fat_pct": 19.0},
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["body_metrics"]["body_fat_pct"]["body_fat_pct"] == 19.0


def test_patient_bulk_create_ignores_supplied_patient_id(client, app, patient, patient_headers):
    """Patients always create for themselves; supplied patient_id is overridden."""
    with app.app_context():
        other = User.query.filter_by(email="other_bulk@bt.app").first()
        if not other:
            other = User(
                email="other_bulk@bt.app",
                first_name="Other",
                last_name="Bulk",
                role="patient",
                email_verified=True,
            )
            other.set_password("Other1234!")
            _db.session.add(other)
            _db.session.flush()
            _db.session.add(Profile(user_id=other.id))
            _db.session.commit()
        other_id = str(other.id)
        my_id = str(patient.id)

    resp = client.post(
        "/api/v1/weigh-ins",
        headers=patient_headers,
        json={
            "patient_id": other_id,
            "weight_kg": 70.0,
            "recorded_at": "2098-03-01T10:00:00+00:00",
            "body_metrics": {"body_fat_pct": 20.0},
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["data"]["patient_id"] == my_id
