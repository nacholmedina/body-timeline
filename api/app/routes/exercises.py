from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.exercise import Exercise, ExerciseRequest
from app.services.rbac import roles_required
from app.utils.errors import validation_error, api_error
from app.utils.validators import get_pagination_params

bp = Blueprint("exercises", __name__)


# ── Exercise catalog ──────────────────────────────────────

@bp.route("", methods=["GET"])
@jwt_required()
def list_exercises():
    query = Exercise.query.filter_by(is_active=True)

    search = request.args.get("search")
    if search:
        query = query.filter(Exercise.name.ilike(f"%{search}%"))

    muscle = request.args.get("muscle_group")
    if muscle:
        query = query.filter_by(muscle_group=muscle)

    query = query.order_by(Exercise.name)
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[e.to_dict() for e in items], page=page, limit=limit, total=total)


@bp.route("", methods=["POST"])
@roles_required("devadmin")
def create_exercise():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return validation_error("Name is required", "name")

    ex_type = data.get("exercise_type", "sets_reps")
    if ex_type not in ("duration", "sets_reps", "both"):
        return validation_error("Invalid exercise_type", "exercise_type")

    if Exercise.query.filter_by(name=name).first():
        return api_error("Exercise with this name already exists", 409)

    exercise = Exercise(
        name=name,
        description=data.get("description"),
        exercise_type=ex_type,
        muscle_group=data.get("muscle_group"),
    )
    db.session.add(exercise)
    db.session.commit()
    return jsonify(data=exercise.to_dict()), 201


@bp.route("/<uuid:exercise_id>", methods=["PATCH"])
@roles_required("devadmin")
def update_exercise(exercise_id):
    exercise = db.session.get(Exercise, exercise_id)
    if not exercise:
        return api_error("Exercise not found", 404)

    data = request.get_json(silent=True) or {}
    if "name" in data:
        exercise.name = data["name"].strip()
    if "description" in data:
        exercise.description = data["description"]
    if "exercise_type" in data:
        exercise.exercise_type = data["exercise_type"]
    if "muscle_group" in data:
        exercise.muscle_group = data["muscle_group"]
    if "is_active" in data:
        exercise.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify(data=exercise.to_dict())


# ── Exercise requests ─────────────────────────────────────

@bp.route("/requests", methods=["GET"])
@jwt_required()
def list_requests():
    query = ExerciseRequest.query

    if current_user.role not in ("devadmin",):
        query = query.filter_by(requested_by=current_user.id)

    status = request.args.get("status")
    if status in ("pending", "approved", "rejected"):
        query = query.filter_by(status=status)

    query = query.order_by(ExerciseRequest.created_at.desc())
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[r.to_dict() for r in items], page=page, limit=limit, total=total)


@bp.route("/requests", methods=["POST"])
@jwt_required()
def create_request():
    if current_user.role not in ("patient", "professional", "devadmin"):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return validation_error("Name is required", "name")

    ex_type = data.get("exercise_type", "sets_reps")
    if ex_type not in ("duration", "sets_reps", "both"):
        return validation_error("Invalid exercise_type", "exercise_type")

    req = ExerciseRequest(
        requested_by=current_user.id,
        name=name,
        description=data.get("description"),
        exercise_type=ex_type,
    )
    db.session.add(req)
    db.session.commit()
    return jsonify(data=req.to_dict()), 201


@bp.route("/requests/<uuid:request_id>/review", methods=["POST"])
@roles_required("devadmin")
def review_request(request_id):
    req = db.session.get(ExerciseRequest, request_id)
    if not req:
        return api_error("Request not found", 404)
    if req.status != "pending":
        return api_error("Request already reviewed", 400)

    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action not in ("approve", "reject"):
        return validation_error("action must be 'approve' or 'reject'")

    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)

    if action == "approve":
        req.status = "approved"
        exercise = Exercise(
            name=req.name,
            description=req.description,
            exercise_type=req.exercise_type,
        )
        db.session.add(exercise)
        db.session.flush()
        req.created_exercise_id = exercise.id
    else:
        req.status = "rejected"

    db.session.commit()
    return jsonify(data=req.to_dict())
