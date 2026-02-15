from datetime import datetime, timezone, timedelta

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.weigh_in import WeighIn
from app.models.goal import Goal
from app.models.meal import Meal
from app.models.workout import Workout
from app.models.appointment import Appointment
from app.models.notification import Notification, NotificationRecipient
from app.models.user import User, ProfessionalPatient
from app.models.patient_invitation import PatientInvitation
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids

bp = Blueprint("dashboard", __name__)


@bp.route("/professional-summary", methods=["GET"])
@jwt_required()
def professional_summary():
    """Summary for professional / admin dashboard."""
    if current_user.role not in ("professional", "devadmin"):
        return jsonify(error="Forbidden"), 403

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    # Patient count
    if current_user.role == "professional":
        patient_count = ProfessionalPatient.query.filter_by(
            professional_id=current_user.id, is_active=True
        ).count()
    else:
        patient_count = User.query.filter_by(role="patient", is_active=True).count()

    # Today's appointments
    appt_query = Appointment.query.filter(
        Appointment.scheduled_at >= today_start,
        Appointment.scheduled_at < today_end,
        Appointment.status == "scheduled",
    )
    if current_user.role == "professional":
        appt_query = appt_query.filter_by(professional_id=current_user.id)
    todays_appointments = appt_query.order_by(Appointment.scheduled_at.asc()).all()

    # Upcoming appointments (next 7 days, excluding today)
    week_end = today_start + timedelta(days=7)
    upcoming_query = Appointment.query.filter(
        Appointment.scheduled_at >= today_end,
        Appointment.scheduled_at < week_end,
        Appointment.status == "scheduled",
    )
    if current_user.role == "professional":
        upcoming_query = upcoming_query.filter_by(professional_id=current_user.id)
    upcoming_count = upcoming_query.count()

    # Pending invitations
    pending_invitations = PatientInvitation.query.filter_by(
        professional_id=current_user.id, status="pending"
    ).count() if current_user.role == "professional" else 0

    # Recent patient activity (meals + workouts in last 7 days)
    patient_ids = get_accessible_patient_ids(current_user)
    week_ago = now - timedelta(days=7)

    recent_meals_q = Meal.query.filter(Meal.eaten_at >= week_ago)
    recent_workouts_q = Workout.query.filter(Workout.started_at >= week_ago)
    if patient_ids is not None:
        recent_meals_q = recent_meals_q.filter(Meal.patient_id.in_(patient_ids))
        recent_workouts_q = recent_workouts_q.filter(Workout.patient_id.in_(patient_ids))

    recent_meals = recent_meals_q.count()
    recent_workouts = recent_workouts_q.count()

    return jsonify(
        patient_count=patient_count,
        todays_appointments=[a.to_dict() for a in todays_appointments],
        upcoming_appointments_count=upcoming_count,
        pending_invitations=pending_invitations,
        recent_meals_7d=recent_meals,
        recent_workouts_7d=recent_workouts,
    )


@bp.route("/summary", methods=["GET"])
@jwt_required()
def summary():
    """Summary counts for dashboard widgets."""
    patient_id = request.args.get("patient_id")
    if current_user.role == "patient":
        patient_id = str(current_user.id)
    if not patient_id:
        return jsonify(error="patient_id required"), 400
    if not can_access_patient_data(current_user, patient_id):
        return jsonify(error="Forbidden"), 403

    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    meals_count = Meal.query.filter(
        Meal.patient_id == patient_id, Meal.eaten_at >= month_start
    ).count()

    workouts_count = Workout.query.filter(
        Workout.patient_id == patient_id, Workout.started_at >= month_start
    ).count()

    goals_total = Goal.query.filter_by(patient_id=patient_id).count()
    goals_done = Goal.query.filter_by(patient_id=patient_id, is_completed=True).count()

    next_appointment = (
        Appointment.query.filter(
            Appointment.patient_id == patient_id,
            Appointment.scheduled_at >= now,
            Appointment.status == "scheduled",
        )
        .order_by(Appointment.scheduled_at.asc())
        .first()
    )

    unread_notifications = NotificationRecipient.query.filter_by(
        patient_id=patient_id, is_read=False
    ).count()

    return jsonify(
        meals_this_month=meals_count,
        workouts_this_month=workouts_count,
        goals_total=goals_total,
        goals_completed=goals_done,
        unread_notifications=unread_notifications,
        next_appointment=next_appointment.to_dict() if next_appointment else None,
    )


@bp.route("/weight-series", methods=["GET"])
@jwt_required()
def weight_series():
    """Weight over time for chart."""
    patient_id = request.args.get("patient_id")
    if current_user.role == "patient":
        patient_id = str(current_user.id)
    if not patient_id:
        return jsonify(error="patient_id required"), 400
    if not can_access_patient_data(current_user, patient_id):
        return jsonify(error="Forbidden"), 403

    days = int(request.args.get("days", 90))
    since = datetime.now(timezone.utc) - timedelta(days=days)

    weigh_ins = (
        WeighIn.query.filter(
            WeighIn.patient_id == patient_id, WeighIn.recorded_at >= since
        )
        .order_by(WeighIn.recorded_at.asc())
        .all()
    )

    return jsonify(
        data=[
            {"date": w.recorded_at.isoformat(), "weight_kg": float(w.weight_kg)}
            for w in weigh_ins
        ]
    )


@bp.route("/activity-series", methods=["GET"])
@jwt_required()
def activity_series():
    """Workouts per week for chart."""
    patient_id = request.args.get("patient_id")
    if current_user.role == "patient":
        patient_id = str(current_user.id)
    if not patient_id:
        return jsonify(error="patient_id required"), 400
    if not can_access_patient_data(current_user, patient_id):
        return jsonify(error="Forbidden"), 403

    weeks = int(request.args.get("weeks", 12))
    since = datetime.now(timezone.utc) - timedelta(weeks=weeks)

    workouts = (
        Workout.query.filter(
            Workout.patient_id == patient_id, Workout.started_at >= since
        )
        .order_by(Workout.started_at.asc())
        .all()
    )

    # Group by ISO week
    weekly = {}
    for w in workouts:
        year, week_num, _ = w.started_at.isocalendar()
        key = f"{year}-W{week_num:02d}"
        weekly[key] = weekly.get(key, 0) + 1

    return jsonify(
        data=[{"week": k, "count": v} for k, v in sorted(weekly.items())]
    )


@bp.route("/goals-series", methods=["GET"])
@jwt_required()
def goals_series():
    """Goals completed over time."""
    patient_id = request.args.get("patient_id")
    if current_user.role == "patient":
        patient_id = str(current_user.id)
    if not patient_id:
        return jsonify(error="patient_id required"), 400
    if not can_access_patient_data(current_user, patient_id):
        return jsonify(error="Forbidden"), 403

    goals = (
        Goal.query.filter(
            Goal.patient_id == patient_id, Goal.is_completed == True
        )
        .order_by(Goal.completed_at.asc())
        .all()
    )

    return jsonify(
        data=[
            {"date": g.completed_at.isoformat(), "title": g.title}
            for g in goals if g.completed_at
        ]
    )
