from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import func, select

from app.extensions import db
from app.models.weigh_in import WeighIn
from app.models.goal import Goal
from app.models.meal import Meal
from app.models.exercise_log import ExerciseLog
from app.models.appointment import Appointment
from app.models.notification import Notification, NotificationRecipient
from app.models.user import User, ProfessionalPatient
from app.models.patient_invitation import PatientInvitation
from app.services.body_metrics import METRICS as BODY_METRICS
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids

bp = Blueprint("dashboard", __name__)


# ── Time-window helpers ──────────────────────────────────────────────────────

def _resolve_tz_window(tz_name):
    """Resolve "now / today-start / today-end / month-start" honoring tz_name.

    Returns all four as UTC-aware datetimes. Falls back to UTC if tz_name is
    missing or invalid — the previous behavior.
    """
    now = datetime.now(timezone.utc)
    if tz_name:
        try:
            tz = ZoneInfo(tz_name)
            now_local = now.astimezone(tz)
            today_local = now_local.replace(hour=0, minute=0, second=0, microsecond=0)
            month_local = today_local.replace(day=1)
            return (
                now,
                today_local.astimezone(timezone.utc),
                (today_local + timedelta(days=1)).astimezone(timezone.utc),
                month_local.astimezone(timezone.utc),
            )
        except Exception:
            pass
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return now, today, today + timedelta(days=1), today.replace(day=1)


def _resolve_patient_id():
    """Return (patient_id, error_response). Patients are pinned to themselves."""
    patient_id = request.args.get("patient_id")
    if current_user.role == "patient":
        patient_id = str(current_user.id)
    if not patient_id:
        return None, (jsonify(error="patient_id required"), 400)
    if not can_access_patient_data(current_user, patient_id):
        return None, (jsonify(error="Forbidden"), 403)
    return patient_id, None


# ── Patient-summary helpers ──────────────────────────────────────────────────

def _patient_summary(patient_id, tz_name):
    """Build the patient summary using exactly 2 DB roundtrips:

    1) one combined SELECT with five scalar subqueries for the counts
    2) one SELECT for the next appointment row

    Was 6 separate queries before; the dashboard fires this on every load so
    the round-trip savings show up on every paint.
    """
    now, _today_start, _today_end, month_start = _resolve_tz_window(tz_name)

    counts_stmt = select(
        select(func.count())
            .select_from(Meal)
            .where(Meal.patient_id == patient_id, Meal.eaten_at >= month_start)
            .scalar_subquery()
            .label("meals_count"),
        select(func.count())
            .select_from(ExerciseLog)
            .where(ExerciseLog.patient_id == patient_id, ExerciseLog.performed_at >= month_start)
            .scalar_subquery()
            .label("workouts_count"),
        select(func.count())
            .select_from(Goal)
            .where(Goal.patient_id == patient_id)
            .scalar_subquery()
            .label("goals_total"),
        select(func.count())
            .select_from(Goal)
            .where(Goal.patient_id == patient_id, Goal.is_completed.is_(True))
            .scalar_subquery()
            .label("goals_done"),
        select(func.count())
            .select_from(NotificationRecipient)
            .where(
                NotificationRecipient.patient_id == patient_id,
                NotificationRecipient.is_read.is_(False),
            )
            .scalar_subquery()
            .label("unread_notifications"),
    )
    counts = db.session.execute(counts_stmt).one()

    next_appointment = (
        Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.scheduled_at >= now,
            Appointment.status == "scheduled",
        )
        .order_by(Appointment.scheduled_at.asc())
        .first()
    )

    return {
        "meals_this_month": counts.meals_count,
        "workouts_this_month": counts.workouts_count,
        "goals_total": counts.goals_total,
        "goals_completed": counts.goals_done,
        "unread_notifications": counts.unread_notifications,
        "next_appointment": next_appointment.to_dict() if next_appointment else None,
    }


def _weight_series(patient_id, days=90):
    """Return [{date, weight_kg}] without hydrating full ORM rows."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = (
        db.session.query(WeighIn.recorded_at, WeighIn.weight_kg)
        .filter(WeighIn.patient_id == patient_id, WeighIn.recorded_at >= since)
        .order_by(WeighIn.recorded_at.asc())
        .all()
    )
    return [
        {"date": recorded_at.isoformat(), "weight_kg": float(weight_kg)}
        for recorded_at, weight_kg in rows
    ]


def _body_metrics_series(patient_id, days=365):
    """Return per-metric [{date, value}] arrays the dashboard chart can plot.

    Five small queries (one per metric table). The frontend picks which one
    to render based on the active selector chip.
    """
    since = datetime.now(timezone.utc) - timedelta(days=days)
    out = {}
    for spec in BODY_METRICS:
        value_col = getattr(spec.model, spec.column)
        rows = (
            db.session.query(spec.model.recorded_at, value_col)
            .filter(spec.model.patient_id == patient_id, spec.model.recorded_at >= since)
            .order_by(spec.model.recorded_at.asc())
            .all()
        )
        out[spec.column] = [
            {"date": recorded_at.isoformat(), "value": float(value)}
            for recorded_at, value in rows
        ]
    return out


def _activity_series(patient_id, weeks=12):
    """Exercises grouped by ISO week. Replaces the long-broken empty-list stub."""
    since = datetime.now(timezone.utc) - timedelta(weeks=weeks)
    rows = (
        db.session.query(ExerciseLog.performed_at)
        .filter(ExerciseLog.patient_id == patient_id, ExerciseLog.performed_at >= since)
        .all()
    )
    weekly = {}
    for (performed_at,) in rows:
        year, week_num, _ = performed_at.isocalendar()
        key = f"{year}-W{week_num:02d}"
        weekly[key] = weekly.get(key, 0) + 1
    return [{"week": k, "count": v} for k, v in sorted(weekly.items())]


def _recent_notifications(patient_id, limit):
    """Same shape the standalone /notifications listing returns for a patient."""
    notifs = (
        db.session.query(Notification)
        .join(NotificationRecipient)
        .filter(NotificationRecipient.patient_id == patient_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .all()
    )
    out = []
    for n in notifs:
        data = n.to_dict(include_recipients=False)
        recip = NotificationRecipient.query.filter_by(
            notification_id=n.id, patient_id=patient_id
        ).first()
        if recip:
            data["is_read"] = recip.is_read
            data["read_at"] = recip.read_at.isoformat() if recip.read_at else None
        out.append(data)
    return out


# ── Routes ───────────────────────────────────────────────────────────────────

@bp.route("/professional-summary", methods=["GET"])
@jwt_required()
def professional_summary():
    """Summary for professional / admin dashboard."""
    if current_user.role not in ("professional", "devadmin"):
        return jsonify(error="Forbidden"), 403

    now, today_start, today_end, _month_start = _resolve_tz_window(request.args.get("tz"))

    if current_user.role == "professional":
        patient_count = ProfessionalPatient.query.filter_by(
            professional_id=current_user.id, is_active=True
        ).count()
    else:
        patient_count = User.query.filter_by(role="patient", is_active=True).count()

    appt_query = Appointment.query.filter(
        Appointment.scheduled_at >= today_start,
        Appointment.scheduled_at < today_end,
        Appointment.status == "scheduled",
    )
    if current_user.role == "professional":
        appt_query = appt_query.filter_by(professional_id=current_user.id)
    todays_appointments = appt_query.order_by(Appointment.scheduled_at.asc()).all()

    week_end = today_start + timedelta(days=7)
    upcoming_query = Appointment.query.filter(
        Appointment.scheduled_at >= today_end,
        Appointment.scheduled_at < week_end,
        Appointment.status == "scheduled",
    )
    if current_user.role == "professional":
        upcoming_query = upcoming_query.filter_by(professional_id=current_user.id)
    upcoming_count = upcoming_query.count()

    pending_invitations = (
        PatientInvitation.query.filter_by(
            professional_id=current_user.id, status="pending"
        ).count()
        if current_user.role == "professional"
        else 0
    )

    patient_ids = get_accessible_patient_ids(current_user)
    week_ago = now - timedelta(days=7)

    recent_meals_q = Meal.query.filter(Meal.eaten_at >= week_ago)
    recent_workouts_q = ExerciseLog.query.filter(ExerciseLog.performed_at >= week_ago)
    if patient_ids is not None:
        recent_meals_q = recent_meals_q.filter(Meal.patient_id.in_(patient_ids))
        recent_workouts_q = recent_workouts_q.filter(ExerciseLog.patient_id.in_(patient_ids))

    return jsonify(
        patient_count=patient_count,
        todays_appointments=[a.to_dict() for a in todays_appointments],
        upcoming_appointments_count=upcoming_count,
        pending_invitations=pending_invitations,
        recent_meals_7d=recent_meals_q.count(),
        recent_workouts_7d=recent_workouts_q.count(),
    )


@bp.route("/summary", methods=["GET"])
@jwt_required()
def summary():
    patient_id, err = _resolve_patient_id()
    if err:
        return err
    return jsonify(_patient_summary(patient_id, request.args.get("tz")))


@bp.route("/weight-series", methods=["GET"])
@jwt_required()
def weight_series():
    patient_id, err = _resolve_patient_id()
    if err:
        return err
    days = int(request.args.get("days", 90))
    return jsonify(data=_weight_series(patient_id, days))


@bp.route("/activity-series", methods=["GET"])
@jwt_required()
def activity_series():
    patient_id, err = _resolve_patient_id()
    if err:
        return err
    weeks = int(request.args.get("weeks", 12))
    return jsonify(data=_activity_series(patient_id, weeks))


@bp.route("/init", methods=["GET"])
@jwt_required()
def init_bundle():
    """One-shot dashboard payload — replaces 4 separate frontend calls.

    Returns: {summary, weight_series, activity_series, notifications}.
    The four standalone endpoints stay live for backwards compat and ad-hoc
    refreshes (no caller changes required).
    """
    patient_id, err = _resolve_patient_id()
    if err:
        return err

    days = int(request.args.get("days", 90))
    weeks = int(request.args.get("weeks", 12))
    notif_limit = max(1, min(50, int(request.args.get("notifications_limit", 5))))

    return jsonify(
        summary=_patient_summary(patient_id, request.args.get("tz")),
        weight_series=_weight_series(patient_id, days),
        body_metrics_series=_body_metrics_series(patient_id, days),
        activity_series=_activity_series(patient_id, weeks),
        notifications=_recent_notifications(patient_id, notif_limit),
    )
