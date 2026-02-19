from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.exercise_log import ExerciseLog, ExercisePhoto
from app.models.exercise_definition import ExerciseDefinition
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.services.exercise_validator import validate_measurements
from app.services.storage import get_storage
from app.utils.errors import validation_error, api_error
from app.utils.validators import parse_datetime, get_pagination_params

bp = Blueprint("exercise_logs", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_exercise_logs():
    """List exercise logs with filtering."""
    patient_ids = get_accessible_patient_ids(current_user)
    query = ExerciseLog.query

    if patient_ids is not None:
        query = query.filter(ExerciseLog.patient_id.in_(patient_ids))

    # Filter by specific patient
    pid = request.args.get("patient_id")
    if pid:
        if not can_access_patient_data(current_user, pid):
            return api_error("Forbidden", 403)
        query = query.filter_by(patient_id=pid)

    # Filter by exercise definition
    exercise_id = request.args.get("exercise_definition_id")
    if exercise_id:
        query = query.filter_by(exercise_definition_id=exercise_id)

    # Filter by date range
    from_date = request.args.get("from")
    if from_date:
        dt = parse_datetime(from_date)
        if dt:
            query = query.filter(ExerciseLog.performed_at >= dt)

    to_date = request.args.get("to")
    if to_date:
        dt = parse_datetime(to_date)
        if dt:
            query = query.filter(ExerciseLog.performed_at <= dt)

    # Order by most recent first
    query = query.order_by(ExerciseLog.performed_at.desc())

    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[log.to_dict() for log in items], page=page, limit=limit, total=total)


@bp.route("", methods=["POST"])
@jwt_required()
def create_exercise_log():
    """Log a new exercise."""
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

    # Validate performed_at
    performed_at = parse_datetime(data.get("performed_at"))
    if not performed_at:
        return validation_error("Valid performed_at datetime is required", "performed_at")

    # Get exercise definition or custom exercise
    exercise_definition_id = data.get("exercise_definition_id")
    custom_exercise_name = (data.get("custom_exercise_name") or "").strip()

    exercise_definition = None
    if exercise_definition_id:
        exercise_definition = db.session.get(ExerciseDefinition, exercise_definition_id)
        if not exercise_definition or not exercise_definition.is_active:
            return validation_error("Exercise definition not found", "exercise_definition_id")
    elif not custom_exercise_name:
        return validation_error("Either exercise_definition_id or custom_exercise_name is required")

    # Validate measurements
    measurements = data.get("measurements", {})
    if not isinstance(measurements, dict):
        return validation_error("Measurements must be an object", "measurements")

    # Validate against allowed measurements if using a definition
    allowed_measurements = None
    if exercise_definition:
        allowed_measurements = exercise_definition.get_allowed_measurements()

    is_valid, error_msg = validate_measurements(measurements, allowed_measurements)
    if not is_valid:
        return validation_error(error_msg, "measurements")

    # Create exercise log
    exercise_log = ExerciseLog(
        patient_id=patient_id,
        exercise_definition_id=exercise_definition_id,
        custom_exercise_name=custom_exercise_name,
        custom_exercise_description=data.get("custom_exercise_description"),
        performed_at=performed_at,
        notes=data.get("notes"),
    )
    exercise_log.set_measurements(measurements)

    db.session.add(exercise_log)

    # Update usage count for exercise definition
    if exercise_definition:
        exercise_definition.increment_usage()

    db.session.commit()
    return jsonify(data=exercise_log.to_dict()), 201


@bp.route("/<uuid:log_id>", methods=["GET"])
@jwt_required()
def get_exercise_log(log_id):
    """Get a single exercise log."""
    log = db.session.get(ExerciseLog, log_id)
    if not log:
        return api_error("Exercise log not found", 404)
    if not can_access_patient_data(current_user, log.patient_id):
        return api_error("Forbidden", 403)
    return jsonify(data=log.to_dict())


@bp.route("/<uuid:log_id>", methods=["PATCH"])
@jwt_required()
def update_exercise_log(log_id):
    """Update an exercise log."""
    log = db.session.get(ExerciseLog, log_id)
    if not log:
        return api_error("Exercise log not found", 404)
    if not can_access_patient_data(current_user, log.patient_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}

    # Support changing the exercise definition
    if "exercise_definition_id" in data:
        new_def_id = data["exercise_definition_id"]
        if new_def_id:
            new_def = db.session.get(ExerciseDefinition, new_def_id)
            if not new_def:
                return validation_error("Exercise definition not found", "exercise_definition_id")
            log.exercise_definition_id = new_def_id
            log.custom_exercise_name = None
            log.custom_exercise_description = None
        else:
            # Switching to custom exercise
            log.exercise_definition_id = None

    if "performed_at" in data:
        dt = parse_datetime(data["performed_at"])
        if dt:
            log.performed_at = dt

    if "measurements" in data:
        measurements = data["measurements"]
        if not isinstance(measurements, dict):
            return validation_error("Measurements must be an object", "measurements")

        # Validate against allowed measurements of the (possibly updated) definition
        allowed_measurements = None
        if log.exercise_definition_id:
            definition = db.session.get(ExerciseDefinition, log.exercise_definition_id)
            if definition:
                allowed_measurements = definition.get_allowed_measurements()

        is_valid, error_msg = validate_measurements(measurements, allowed_measurements)
        if not is_valid:
            return validation_error(error_msg, "measurements")

        log.set_measurements(measurements)

    if "notes" in data:
        log.notes = data["notes"]

    if "custom_exercise_name" in data:
        log.custom_exercise_name = data["custom_exercise_name"]

    if "custom_exercise_description" in data:
        log.custom_exercise_description = data["custom_exercise_description"]

    db.session.commit()
    return jsonify(data=log.to_dict())


@bp.route("/<uuid:log_id>", methods=["DELETE"])
@jwt_required()
def delete_exercise_log(log_id):
    """Delete an exercise log."""
    log = db.session.get(ExerciseLog, log_id)
    if not log:
        return api_error("Exercise log not found", 404)
    if not can_access_patient_data(current_user, log.patient_id):
        return api_error("Forbidden", 403)

    db.session.delete(log)
    db.session.commit()
    return jsonify(message="Exercise log deleted")


@bp.route("/<uuid:log_id>/photos", methods=["POST"])
@jwt_required()
def upload_exercise_photo(log_id):
    """Upload a photo for an exercise log."""
    log = db.session.get(ExerciseLog, log_id)
    if not log:
        return api_error("Exercise log not found", 404)
    if not can_access_patient_data(current_user, log.patient_id):
        return api_error("Forbidden", 403)

    if "photo" not in request.files:
        return validation_error("Photo file is required", "photo")

    file = request.files["photo"]
    if file.filename == "":
        return validation_error("No file selected", "photo")

    try:
        # Upload to storage
        storage = get_storage()
        result = storage.upload(file, folder="exercise_logs")

        # Create photo record
        photo = ExercisePhoto(
            exercise_log_id=log.id,
            storage_key=result["storage_key"],
            caption=request.form.get("caption"),
            sort_order=len(log.photos),
        )
        db.session.add(photo)
        db.session.commit()

        return jsonify(data=photo.to_dict()), 201
    except Exception as e:
        return api_error(f"Failed to upload photo: {str(e)}", 500)


@bp.route("/<uuid:log_id>/photos/<uuid:photo_id>", methods=["DELETE"])
@jwt_required()
def delete_exercise_photo(log_id, photo_id):
    """Delete an exercise photo."""
    log = db.session.get(ExerciseLog, log_id)
    if not log:
        return api_error("Exercise log not found", 404)
    if not can_access_patient_data(current_user, log.patient_id):
        return api_error("Forbidden", 403)

    photo = db.session.get(ExercisePhoto, photo_id)
    if not photo or str(photo.exercise_log_id) != str(log_id):
        return api_error("Photo not found", 404)

    try:
        # Delete from storage
        storage = get_storage()
        storage.delete(photo.storage_key)
    except Exception:
        pass  # Continue even if storage deletion fails

    db.session.delete(photo)
    db.session.commit()
    return jsonify(message="Photo deleted")
