"""Tests for dashboard endpoints — focused on the bits that just changed:

- /summary now answers via 2 DB roundtrips (combined-aggregate + next_appointment).
  We assert the response shape and counts, not the query plan, so the test stays
  green if SQLAlchemy reshapes the SQL.
- /activity-series used to return [] forever; now actually queries ExerciseLog.
- /init bundles summary + weight + activity + notifications in one call.
- /goals-series is gone (404 now).
"""
from datetime import datetime, timezone, timedelta

import pytest

from app.extensions import db as _db
from app.models.appointment import Appointment
from app.models.body_metric import BodyFatLog, MuscleMassLog
from app.models.exercise_log import ExerciseLog
from app.models.goal import Goal
from app.models.meal import Meal
from app.models.notification import Notification, NotificationRecipient
from app.models.user import User, Profile
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
def seeded_patient_id(app, patient):
    """Seed a fixed dataset for the patient and return their UUID as a string.

    Idempotent — re-running just no-ops. Returning a plain string avoids the
    DetachedInstanceError pattern of handing back ORM objects across contexts.
    """
    with app.app_context():
        marker = User.query.filter_by(email="test_patient@bt.app").one()
        patient_id = str(marker.id)

        already = Meal.query.filter_by(
            patient_id=marker.id, description="dashboard-test-marker"
        ).first()
        if already:
            return patient_id

        now = datetime.now(timezone.utc)
        # 3 meals THIS month
        for i in range(3):
            _db.session.add(
                Meal(
                    patient_id=marker.id,
                    description="dashboard-test-marker" if i == 0 else "x",
                    eaten_at=now - timedelta(days=i),
                )
            )

        # 2 exercise logs in the last 12 weeks, 1 outside (20 weeks ago)
        for i in range(2):
            _db.session.add(
                ExerciseLog(
                    patient_id=marker.id,
                    custom_exercise_name="Run",
                    performed_at=now - timedelta(days=i),
                )
            )
        _db.session.add(
            ExerciseLog(
                patient_id=marker.id,
                custom_exercise_name="Old",
                performed_at=now - timedelta(weeks=20),
            )
        )

        # 3 goals total, 1 completed
        _db.session.add(Goal(patient_id=marker.id, title="A", is_completed=False))
        _db.session.add(Goal(patient_id=marker.id, title="B", is_completed=False))
        _db.session.add(
            Goal(patient_id=marker.id, title="C", is_completed=True, completed_at=now)
        )

        # 2 weigh-ins inside the 365-day window
        _db.session.add(WeighIn(patient_id=marker.id, weight_kg=80.0, recorded_at=now - timedelta(days=10)))
        _db.session.add(WeighIn(patient_id=marker.id, weight_kg=79.5, recorded_at=now - timedelta(days=5)))

        _db.session.commit()
        return patient_id


# ── /summary ─────────────────────────────────────────────────────────────────

def test_summary_returns_expected_shape(client, app, seeded_patient_id, patient_headers):
    resp = client.get("/api/v1/dashboard/summary", headers=patient_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    # Shape preserved across the refactor — frontend already binds these keys.
    for key in (
        "meals_this_month",
        "workouts_this_month",
        "goals_total",
        "goals_completed",
        "unread_notifications",
        "next_appointment",
    ):
        assert key in data

    # Counts reflect the seeded data (these are >= because the shared DB may
    # have residue from earlier tests; we only assert lower bounds tied to seed).
    assert data["goals_total"] >= 3
    assert data["goals_completed"] >= 1
    assert data["meals_this_month"] >= 3
    assert data["workouts_this_month"] >= 2


def test_patient_role_pins_summary_to_self(client, app, patient_headers):
    """A patient passing someone else's patient_id still gets THEIR own summary —
    the route overrides patient_id from the JWT, never trusts the query param."""
    with app.app_context():
        other = User.query.filter_by(email="other_dashboard@bt.app").first()
        if not other:
            other = User(
                email="other_dashboard@bt.app",
                first_name="O",
                last_name="O",
                role="patient",
                email_verified=True,
            )
            other.set_password("Other1234!")
            _db.session.add(other)
            _db.session.flush()
            _db.session.add(Profile(user_id=other.id))
            _db.session.commit()
        other_id = str(other.id)

    resp = client.get(
        f"/api/v1/dashboard/summary?patient_id={other_id}",
        headers=patient_headers,
    )
    # Should NOT 403 even though the supplied id isn't theirs — the route
    # silently rebinds to current_user. Just confirm it returns valid data.
    assert resp.status_code == 200
    data = resp.get_json()
    assert "meals_this_month" in data


# ── /activity-series (was broken) ────────────────────────────────────────────

def test_activity_series_actually_returns_exercise_logs(
    client, seeded_patient_id, patient_headers
):
    """Before the fix, this endpoint always returned []."""
    resp = client.get(
        "/api/v1/dashboard/activity-series?weeks=12", headers=patient_headers
    )
    assert resp.status_code == 200
    data = resp.get_json()["data"]
    # Seed put 2 exercise logs in the last few days; older ones (20 weeks ago)
    # are outside the 12-week window.
    assert len(data) >= 1
    total = sum(item["count"] for item in data)
    assert total >= 2
    # Each item is {week: "YYYY-Www", count: N}
    for item in data:
        assert "week" in item and item["week"].startswith("20")
        assert "count" in item and item["count"] >= 1


# ── /init (new bundle) ───────────────────────────────────────────────────────

def test_init_returns_all_sections(client, seeded_patient_id, patient_headers):
    resp = client.get(
        "/api/v1/dashboard/init?days=365&weeks=12&notifications_limit=5",
        headers=patient_headers,
    )
    assert resp.status_code == 200
    bundle = resp.get_json()
    assert "summary" in bundle
    assert "weight_series" in bundle
    assert "body_metrics_series" in bundle
    assert "activity_series" in bundle
    assert "notifications" in bundle

    # Same shape as /summary
    assert "meals_this_month" in bundle["summary"]

    # Weight series rendered without ORM hydration but should still work
    assert isinstance(bundle["weight_series"], list)
    assert all("date" in p and "weight_kg" in p for p in bundle["weight_series"])
    assert len(bundle["weight_series"]) >= 2  # from seed

    # body_metrics_series: dict keyed by metric column, every metric must be
    # present so the frontend dropdown stays stable even for empty metrics.
    bms = bundle["body_metrics_series"]
    assert isinstance(bms, dict)
    assert set(bms.keys()) == {"body_fat_pct", "muscle_mass_kg", "waist_cm", "hips_cm", "neck_cm"}
    for arr in bms.values():
        assert isinstance(arr, list)
        for point in arr:
            assert "date" in point and "value" in point

    # Activity series: ExerciseLog-backed, not the old empty stub
    assert isinstance(bundle["activity_series"], list)


def test_init_body_metrics_series_returns_logged_values(
    client, app, seeded_patient_id, patient_headers
):
    """Logged body-metric entries land in the right per-metric bucket and only
    those metrics' buckets — empty metrics stay empty."""
    now = datetime.now(timezone.utc)
    with app.app_context():
        _db.session.add(
            BodyFatLog(
                patient_id=seeded_patient_id,
                body_fat_pct=21.5,
                recorded_at=now - timedelta(days=2),
            )
        )
        _db.session.add(
            MuscleMassLog(
                patient_id=seeded_patient_id,
                muscle_mass_kg=64.0,
                recorded_at=now - timedelta(days=1),
            )
        )
        _db.session.commit()

    resp = client.get("/api/v1/dashboard/init?days=365", headers=patient_headers)
    bms = resp.get_json()["body_metrics_series"]
    bf_values = [p["value"] for p in bms["body_fat_pct"]]
    mm_values = [p["value"] for p in bms["muscle_mass_kg"]]
    assert 21.5 in bf_values
    assert 64.0 in mm_values
    # Waist had nothing logged in this test; bucket may be empty or contain
    # rows from other tests sharing the DB — at minimum, no 21.5 leak.
    waist_values = [p["value"] for p in bms["waist_cm"]]
    assert 21.5 not in waist_values


def test_init_matches_individual_endpoints(
    client, seeded_patient_id, patient_headers
):
    """The bundle must produce equivalent data to calling the four endpoints."""
    bundle = client.get(
        "/api/v1/dashboard/init?days=365&weeks=12", headers=patient_headers
    ).get_json()

    summary_alone = client.get("/api/v1/dashboard/summary", headers=patient_headers).get_json()
    weights_alone = client.get(
        "/api/v1/dashboard/weight-series?days=365", headers=patient_headers
    ).get_json()
    activity_alone = client.get(
        "/api/v1/dashboard/activity-series?weeks=12", headers=patient_headers
    ).get_json()

    # Counts must match
    assert bundle["summary"]["meals_this_month"] == summary_alone["meals_this_month"]
    assert bundle["summary"]["goals_total"] == summary_alone["goals_total"]
    assert bundle["weight_series"] == weights_alone["data"]
    assert bundle["activity_series"] == activity_alone["data"]


def test_init_includes_recent_notifications_with_read_state(
    client, app, seeded_patient_id, patient_headers
):
    """Notifications come back in the same shape the standalone /notifications
    list returns for a patient — including is_read."""
    with app.app_context():
        # Make a professional + a notification addressed to the seeded patient.
        author = User.query.filter_by(email="dash_notif_author@bt.app").first()
        if not author:
            author = User(
                email="dash_notif_author@bt.app",
                first_name="Dash",
                last_name="Author",
                role="professional",
                email_verified=True,
            )
            author.set_password("Author12!")
            _db.session.add(author)
            _db.session.flush()
            _db.session.add(Profile(user_id=author.id))
        n = Notification(author_id=author.id, title="hello", body="world")
        _db.session.add(n)
        _db.session.flush()
        _db.session.add(NotificationRecipient(notification_id=n.id, patient_id=seeded_patient_id))
        _db.session.commit()

    resp = client.get("/api/v1/dashboard/init", headers=patient_headers)
    assert resp.status_code == 200
    notifs = resp.get_json()["notifications"]
    assert isinstance(notifs, list)
    assert any(n["title"] == "hello" for n in notifs)
    # is_read enrichment is what the frontend reads
    assert all("is_read" in n for n in notifs)


# ── /goals-series should be gone ─────────────────────────────────────────────

def test_goals_series_is_deleted(client, patient_headers):
    resp = client.get("/api/v1/dashboard/goals-series", headers=patient_headers)
    assert resp.status_code == 404
