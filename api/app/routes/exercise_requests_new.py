from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.exercise_request import ExerciseRequest
from app.models.exercise_definition import ExerciseDefinition
from app.services.rbac import roles_required
from app.services.exercise_validator import validate_allowed_measurements
from app.services.exercise_notifications import notify_devadmins_new_exercise_request, notify_requester_exercise_reviewed
from app.utils.errors import validation_error, api_error
from app.utils.validators import get_pagination_params

bp = Blueprint("exercise_requests_new", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_exercise_requests():
    """List exercise requests."""
    query = ExerciseRequest.query

    # Filter by requester if not devadmin
    if current_user.role != "devadmin":
        query = query.filter_by(requested_by=current_user.id)

    # Filter by status
    status = request.args.get("status")
    if status in ("pending", "approved", "rejected"):
        query = query.filter_by(status=status)

    query = query.order_by(ExerciseRequest.created_at.desc())
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[r.to_dict() for r in items], page=page, limit=limit, total=total)


@bp.route("", methods=["POST"])
@jwt_required()
def create_exercise_request():
    """Request a new exercise to be added to the catalog."""
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return validation_error("Name is required", "name")

    # Validate category
    category = data.get("category", "general")
    if category not in ("cardio", "strength", "sports", "flexibility", "general"):
        return validation_error("Invalid category", "category")

    # Validate suggested measurements (optional)
    suggested_measurements = data.get("suggested_measurements", [])
    if suggested_measurements:
        is_valid, error_msg = validate_allowed_measurements(suggested_measurements)
        if not is_valid:
            return validation_error(error_msg, "suggested_measurements")

    # Create request
    req = ExerciseRequest(
        requested_by=current_user.id,
        name=name,
        category=category,
        description=data.get("description"),
    )
    if suggested_measurements:
        req.set_suggested_measurements(suggested_measurements)

    db.session.add(req)
    db.session.flush()

    # Notify all devadmins
    notify_devadmins_new_exercise_request(req, current_user)

    db.session.commit()
    return jsonify(data=req.to_dict()), 201


@bp.route("/<uuid:request_id>/review", methods=["POST"])
@roles_required("devadmin")
def review_exercise_request(request_id):
    """Approve or reject an exercise request (devadmin only)."""
    req = db.session.get(ExerciseRequest, request_id)
    if not req:
        return api_error("Request not found", 404)
    if req.status != "pending":
        return api_error("Request already reviewed", 400)

    data = request.get_json(silent=True) or {}
    action = data.get("action")
    if action not in ("approve", "reject"):
        return validation_error("action must be 'approve' or 'reject'", "action")

    req.reviewed_by = current_user.id
    req.reviewed_at = datetime.now(timezone.utc)

    if action == "approve":
        req.status = "approved"

        # Create the exercise definition
        exercise = ExerciseDefinition(
            name=req.name,
            category=req.category,
            description=req.description,
            is_system=False,
            created_by=req.requested_by,
        )

        # Use suggested measurements or default to duration
        measurements = req.get_suggested_measurements()
        if not measurements:
            measurements = ["duration"]
        exercise.set_allowed_measurements(measurements)

        db.session.add(exercise)
        db.session.flush()
        req.created_exercise_id = exercise.id

        # Notify requester of approval
        notify_requester_exercise_reviewed(req, current_user, approved=True)
    else:
        req.status = "rejected"
        req.rejection_reason = data.get("reason")

        # Notify requester of rejection
        notify_requester_exercise_reviewed(req, current_user, approved=False)

    db.session.commit()
    return jsonify(data=req.to_dict())
