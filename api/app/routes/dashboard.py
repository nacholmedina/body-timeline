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
from app.services.rbac import can_access_patient_data

bp = Blueprint("dashboard", __name__)


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
