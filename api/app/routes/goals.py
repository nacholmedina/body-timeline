from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.goal import Goal
from app.models.notification import Notification, NotificationRecipient
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.utils.errors import validation_error, api_error
from app.utils.validators import parse_date, get_pagination_params

bp = Blueprint("goals", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_goals():
    patient_ids = get_accessible_patient_ids(current_user)
    query = Goal.query

    if patient_ids is not None:
        query = query.filter(Goal.patient_id.in_(patient_ids))

    pid = request.args.get("patient_id")
    if pid:
        if not can_access_patient_data(current_user, pid):
            return api_error("Forbidden", 403)
        query = query.filter_by(patient_id=pid)

    period = request.args.get("period")
    if period in ("weekly", "monthly", "yearly"):
        query = query.filter_by(period=period)

    completed = request.args.get("completed")
    if completed == "true":
        query = query.filter_by(is_completed=True)
    elif completed == "false":
        query = query.filter_by(is_completed=False)

    query = query.order_by(Goal.created_at.desc())
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[g.to_dict() for g in items], page=page, limit=limit, total=total)


@bp.route("", methods=["POST"])
@jwt_required()
def create_goal():
    data = request.get_json(silent=True) or {}

    if current_user.role == "patient":
        patient_id = str(current_user.id)
    else:
        patient_id = data.get("patient_id")

    if not patient_id:
        return validation_error("patient_id is required")
    if not can_access_patient_data(current_user, patient_id):
        return api_error("Forbidden", 403)

    title = (data.get("title") or "").strip()
    if not title:
        return validation_error("Title is required", "title")

    period = data.get("period", "weekly")
    if period not in ("weekly", "monthly", "yearly"):
        return validation_error("Period must be weekly, monthly, or yearly", "period")

    goal = Goal(
        patient_id=patient_id,
        title=title,
        description=data.get("description"),
        period=period,
        target_date=parse_date(data.get("target_date")),
    )
    db.session.add(goal)

    # Notify patient when a professional creates a goal for them
    if current_user.role != "patient" and str(current_user.id) != str(patient_id):
        notification = Notification(
            author_id=current_user.id,
            title="goal_created",
            body=title,
        )
        db.session.add(notification)
        db.session.flush()

        recipient = NotificationRecipient(
            notification_id=notification.id,
            patient_id=patient_id,
        )
        db.session.add(recipient)

    db.session.commit()
    return jsonify(data=goal.to_dict()), 201


@bp.route("/<uuid:goal_id>", methods=["GET"])
@jwt_required()
def get_goal(goal_id):
    goal = db.session.get(Goal, goal_id)
    if not goal:
        return api_error("Goal not found", 404)
    if not can_access_patient_data(current_user, goal.patient_id):
        return api_error("Forbidden", 403)
    return jsonify(data=goal.to_dict())


@bp.route("/<uuid:goal_id>", methods=["PATCH"])
@jwt_required()
def update_goal(goal_id):
    goal = db.session.get(Goal, goal_id)
    if not goal:
        return api_error("Goal not found", 404)
    if not can_access_patient_data(current_user, goal.patient_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    if "title" in data:
        goal.title = data["title"].strip()
    if "description" in data:
        goal.description = data["description"]
    if "period" in data and data["period"] in ("weekly", "monthly", "yearly"):
        goal.period = data["period"]
    if "target_date" in data:
        goal.target_date = parse_date(data["target_date"])

    db.session.commit()
    return jsonify(data=goal.to_dict())


@bp.route("/<uuid:goal_id>/toggle", methods=["POST"])
@jwt_required()
def toggle_goal(goal_id):
    goal = db.session.get(Goal, goal_id)
    if not goal:
        return api_error("Goal not found", 404)
    if not can_access_patient_data(current_user, goal.patient_id):
        return api_error("Forbidden", 403)

    goal.is_completed = not goal.is_completed
    goal.completed_at = datetime.now(timezone.utc) if goal.is_completed else None
    db.session.commit()
    return jsonify(data=goal.to_dict())


@bp.route("/<uuid:goal_id>", methods=["DELETE"])
@jwt_required()
def delete_goal(goal_id):
    goal = db.session.get(Goal, goal_id)
    if not goal:
        return api_error("Goal not found", 404)
    if not can_access_patient_data(current_user, goal.patient_id):
        return api_error("Forbidden", 403)

    db.session.delete(goal)
    db.session.commit()
    return jsonify(message="Goal deleted")
