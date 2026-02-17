from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.exercise_routine import ExerciseRoutine, ExerciseRoutineItem
from app.models.exercise_definition import ExerciseDefinition
from app.models.exercise_log import ExerciseLog
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.services.exercise_validator import validate_measurements
from app.utils.errors import validation_error, api_error
from app.utils.validators import parse_datetime, get_pagination_params

bp = Blueprint("exercise_routines", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_exercise_routines():
    """List exercise routines with filtering."""
    patient_ids = get_accessible_patient_ids(current_user)
    query = ExerciseRoutine.query.filter_by(is_active=True)

    if patient_ids is not None:
        query = query.filter(ExerciseRoutine.patient_id.in_(patient_ids))

    # Filter by specific patient
    pid = request.args.get("patient_id")
    if pid:
        if not can_access_patient_data(current_user, pid):
            return api_error("Forbidden", 403)
        query = query.filter_by(patient_id=pid)

    # Order by most recent first
    query = query.order_by(ExerciseRoutine.created_at.desc())

    page, limit, offset = get_pagination_params(request.args, default_limit=50)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[routine.to_dict() for routine in items], page=page, limit=limit, total=total)


@bp.route("", methods=["POST"])
@jwt_required()
def create_exercise_routine():
    """Create a new exercise routine with items."""
    data = request.get_json(silent=True) or {}

    # Determine patient_id
    if current_user.role == "patient":
        patient_id = str(current_user.id)
    else:
        patient_id = data.get("patient_id")

    if not patient_id:
        return validation_error("patient_id is required")
    if not can_access_patient_data(current_user, patient_id):
        return api_error("Forbidden", 403)

    # Validate routine name
    name = (data.get("name") or "").strip()
    if not name:
        return validation_error("Routine name is required", "name")
    if len(name) > 200:
        return validation_error("Routine name too long (max 200 characters)", "name")

    # Validate items
    items_data = data.get("items", [])
    if not isinstance(items_data, list):
        return validation_error("Items must be an array", "items")
    if len(items_data) == 0:
        return validation_error("Routine must have at least one exercise", "items")
    if len(items_data) > 50:
        return validation_error("Routine cannot have more than 50 exercises", "items")

    # Validate each item
    for idx, item in enumerate(items_data):
        if not isinstance(item, dict):
            return validation_error(f"Item {idx} must be an object", "items")

        exercise_def_id = item.get("exercise_definition_id")
        if not exercise_def_id:
            return validation_error(f"Item {idx} missing exercise_definition_id", "items")

        # Verify exercise definition exists
        exercise_def = db.session.get(ExerciseDefinition, exercise_def_id)
        if not exercise_def or not exercise_def.is_active:
            return validation_error(f"Item {idx}: Exercise definition not found", "items")

        # Validate default measurements if provided
        default_measurements = item.get("default_measurements")
        if default_measurements:
            if not isinstance(default_measurements, dict):
                return validation_error(f"Item {idx}: default_measurements must be an object", "items")

            allowed_measurements = exercise_def.get_allowed_measurements()
            is_valid, error_msg = validate_measurements(default_measurements, allowed_measurements)
            if not is_valid:
                return validation_error(f"Item {idx}: {error_msg}", "items")

    # Create routine
    routine = ExerciseRoutine(
        patient_id=patient_id,
        name=name,
        description=data.get("description"),
    )
    db.session.add(routine)
    db.session.flush()

    # Create routine items
    for idx, item in enumerate(items_data):
        routine_item = ExerciseRoutineItem(
            routine_id=routine.id,
            exercise_definition_id=item["exercise_definition_id"],
            sort_order=item.get("sort_order", idx),
            notes=item.get("notes"),
        )

        # Set default measurements if provided
        default_measurements = item.get("default_measurements")
        if default_measurements:
            routine_item.set_default_measurements(default_measurements)

        db.session.add(routine_item)

    db.session.commit()
    return jsonify(data=routine.to_dict()), 201


@bp.route("/<uuid:routine_id>", methods=["GET"])
@jwt_required()
def get_exercise_routine(routine_id):
    """Get a single exercise routine."""
    routine = db.session.get(ExerciseRoutine, routine_id)
    if not routine or not routine.is_active:
        return api_error("Routine not found", 404)
    if not can_access_patient_data(current_user, routine.patient_id):
        return api_error("Forbidden", 403)
    return jsonify(data=routine.to_dict())


@bp.route("/<uuid:routine_id>", methods=["PATCH"])
@jwt_required()
def update_exercise_routine(routine_id):
    """Update an exercise routine."""
    routine = db.session.get(ExerciseRoutine, routine_id)
    if not routine or not routine.is_active:
        return api_error("Routine not found", 404)
    if not can_access_patient_data(current_user, routine.patient_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}

    # Update name
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return validation_error("Routine name is required", "name")
        if len(name) > 200:
            return validation_error("Routine name too long (max 200 characters)", "name")
        routine.name = name

    # Update description
    if "description" in data:
        routine.description = data["description"]

    # Update items if provided
    if "items" in data:
        items_data = data["items"]
        if not isinstance(items_data, list):
            return validation_error("Items must be an array", "items")
        if len(items_data) == 0:
            return validation_error("Routine must have at least one exercise", "items")
        if len(items_data) > 50:
            return validation_error("Routine cannot have more than 50 exercises", "items")

        # Validate each item first
        for idx, item in enumerate(items_data):
            if not isinstance(item, dict):
                return validation_error(f"Item {idx} must be an object", "items")

            exercise_def_id = item.get("exercise_definition_id")
            if not exercise_def_id:
                return validation_error(f"Item {idx} missing exercise_definition_id", "items")

            # Verify exercise definition exists
            exercise_def = db.session.get(ExerciseDefinition, exercise_def_id)
            if not exercise_def or not exercise_def.is_active:
                return validation_error(f"Item {idx}: Exercise definition not found", "items")

            # Validate default measurements if provided
            default_measurements = item.get("default_measurements")
            if default_measurements:
                if not isinstance(default_measurements, dict):
                    return validation_error(f"Item {idx}: default_measurements must be an object", "items")

                allowed_measurements = exercise_def.get_allowed_measurements()
                is_valid, error_msg = validate_measurements(default_measurements, allowed_measurements)
                if not is_valid:
                    return validation_error(f"Item {idx}: {error_msg}", "items")

        # Delete existing items
        for item in routine.items:
            db.session.delete(item)
        db.session.flush()

        # Create new items
        for idx, item in enumerate(items_data):
            routine_item = ExerciseRoutineItem(
                routine_id=routine.id,
                exercise_definition_id=item["exercise_definition_id"],
                sort_order=item.get("sort_order", idx),
                notes=item.get("notes"),
            )

            # Set default measurements if provided
            default_measurements = item.get("default_measurements")
            if default_measurements:
                routine_item.set_default_measurements(default_measurements)

            db.session.add(routine_item)

    db.session.commit()
    return jsonify(data=routine.to_dict())


@bp.route("/<uuid:routine_id>", methods=["DELETE"])
@jwt_required()
def delete_exercise_routine(routine_id):
    """Soft delete an exercise routine."""
    routine = db.session.get(ExerciseRoutine, routine_id)
    if not routine or not routine.is_active:
        return api_error("Routine not found", 404)
    if not can_access_patient_data(current_user, routine.patient_id):
        return api_error("Forbidden", 403)

    # Soft delete
    routine.is_active = False
    db.session.commit()
    return jsonify(message="Routine deleted")


@bp.route("/<uuid:routine_id>/log", methods=["POST"])
@jwt_required()
def log_routine(routine_id):
    """
    Log all exercises from a routine at once.
    Creates individual ExerciseLog entries for each exercise in the routine.
    """
    routine = db.session.get(ExerciseRoutine, routine_id)
    if not routine or not routine.is_active:
        return api_error("Routine not found", 404)
    if not can_access_patient_data(current_user, routine.patient_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}

    # Validate performed_at
    performed_at = parse_datetime(data.get("performed_at"))
    if not performed_at:
        performed_at = datetime.now(timezone.utc)

    # Optional: Allow overriding measurements for specific exercises
    measurements_overrides = data.get("measurements_overrides", {})
    if not isinstance(measurements_overrides, dict):
        return validation_error("measurements_overrides must be an object", "measurements_overrides")

    # Optional notes for the entire routine log
    routine_notes = data.get("notes", "")

    created_logs = []

    # Create ExerciseLog for each item in the routine
    for item in routine.items:
        # Start with default measurements from routine item
        measurements = item.get_default_measurements().copy()

        # Override with user-provided measurements if any
        item_id_str = str(item.id)
        if item_id_str in measurements_overrides:
            override = measurements_overrides[item_id_str]
            if isinstance(override, dict):
                # Validate override measurements
                allowed_measurements = item.exercise_definition.get_allowed_measurements()
                is_valid, error_msg = validate_measurements(override, allowed_measurements)
                if not is_valid:
                    return validation_error(f"Exercise '{item.exercise_definition.name}': {error_msg}", "measurements_overrides")
                measurements.update(override)

        # Create exercise log
        exercise_log = ExerciseLog(
            patient_id=routine.patient_id,
            exercise_definition_id=item.exercise_definition_id,
            performed_at=performed_at,
            notes=f"{routine_notes}\n{item.notes}".strip() if item.notes else routine_notes,
        )
        exercise_log.set_measurements(measurements)

        db.session.add(exercise_log)

        # Increment usage count
        item.exercise_definition.increment_usage()

        created_logs.append(exercise_log)

    db.session.commit()

    return jsonify(
        message=f"Logged {len(created_logs)} exercises from routine",
        data=[log.to_dict(include_photos=False) for log in created_logs]
    ), 201
