from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.exercise_definition import ExerciseDefinition
from app.services.rbac import roles_required
from app.services.exercise_validator import validate_allowed_measurements, get_measurement_schema
from app.utils.errors import validation_error, api_error
from app.utils.validators import get_pagination_params

bp = Blueprint("exercise_definitions", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_exercise_definitions():
    """List exercise definitions with filtering and sorting."""
    query = ExerciseDefinition.query.filter_by(is_active=True)

    # Filter by category
    category = request.args.get("category")
    if category and category in ("cardio", "strength", "sports", "flexibility", "general"):
        query = query.filter_by(category=category)

    # Search by name
    search = request.args.get("search")
    if search:
        query = query.filter(ExerciseDefinition.name.ilike(f"%{search}%"))

    # Sort by usage (most popular) or alphabetically
    sort_by = request.args.get("sort", "usage")
    if sort_by == "usage":
        query = query.order_by(ExerciseDefinition.usage_count.desc(), ExerciseDefinition.name)
    else:  # alphabetical
        query = query.order_by(ExerciseDefinition.name)

    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[e.to_dict() for e in items], page=page, limit=limit, total=total)


@bp.route("/<uuid:exercise_id>", methods=["GET"])
@jwt_required()
def get_exercise_definition(exercise_id):
    """Get a single exercise definition."""
    exercise = db.session.get(ExerciseDefinition, exercise_id)
    if not exercise or not exercise.is_active:
        return api_error("Exercise not found", 404)
    return jsonify(data=exercise.to_dict())


@bp.route("", methods=["POST"])
@roles_required("devadmin")
def create_exercise_definition():
    """Create a new exercise definition (devadmin only)."""
    data = request.get_json(silent=True) or {}

    name = (data.get("name") or "").strip()
    if not name:
        return validation_error("Name is required", "name")

    # Validate category
    category = data.get("category", "general")
    if category not in ("cardio", "strength", "sports", "flexibility", "general"):
        return validation_error("Invalid category", "category")

    # Validate allowed_measurements
    allowed_measurements = data.get("allowed_measurements", [])
    is_valid, error_msg = validate_allowed_measurements(allowed_measurements)
    if not is_valid:
        return validation_error(error_msg, "allowed_measurements")

    # Check for duplicate name
    if ExerciseDefinition.query.filter_by(name=name).first():
        return api_error("Exercise with this name already exists", 409)

    exercise = ExerciseDefinition(
        name=name,
        category=category,
        description=data.get("description"),
        is_system=False,
        created_by=current_user.id,
    )
    exercise.set_allowed_measurements(allowed_measurements)

    db.session.add(exercise)
    db.session.commit()
    return jsonify(data=exercise.to_dict()), 201


@bp.route("/<uuid:exercise_id>", methods=["PATCH"])
@roles_required("devadmin")
def update_exercise_definition(exercise_id):
    """Update an exercise definition (devadmin only)."""
    exercise = db.session.get(ExerciseDefinition, exercise_id)
    if not exercise:
        return api_error("Exercise not found", 404)

    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return validation_error("Name cannot be empty", "name")
        # Check for duplicate (excluding current exercise)
        existing = ExerciseDefinition.query.filter(
            ExerciseDefinition.name == name,
            ExerciseDefinition.id != exercise.id
        ).first()
        if existing:
            return api_error("Exercise with this name already exists", 409)
        exercise.name = name

    if "description" in data:
        exercise.description = data["description"]

    if "category" in data:
        if data["category"] not in ("cardio", "strength", "sports", "flexibility", "general"):
            return validation_error("Invalid category", "category")
        exercise.category = data["category"]

    if "allowed_measurements" in data:
        is_valid, error_msg = validate_allowed_measurements(data["allowed_measurements"])
        if not is_valid:
            return validation_error(error_msg, "allowed_measurements")
        exercise.set_allowed_measurements(data["allowed_measurements"])

    if "is_active" in data:
        exercise.is_active = bool(data["is_active"])

    db.session.commit()
    return jsonify(data=exercise.to_dict())


@bp.route("/<uuid:exercise_id>", methods=["DELETE"])
@roles_required("devadmin")
def delete_exercise_definition(exercise_id):
    """Soft delete an exercise definition (devadmin only)."""
    exercise = db.session.get(ExerciseDefinition, exercise_id)
    if not exercise:
        return api_error("Exercise not found", 404)

    # Soft delete (set is_active=False)
    exercise.is_active = False
    db.session.commit()
    return jsonify(message="Exercise deactivated successfully")


@bp.route("/measurement-schema", methods=["GET"])
@jwt_required()
def measurement_schema():
    """Get the measurement schema for all measurement types."""
    return jsonify(schema=get_measurement_schema())
