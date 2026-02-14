from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.workout import Workout, WorkoutItem, WorkoutPhoto
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.services.storage import get_storage
from app.utils.errors import validation_error, api_error
from app.utils.validators import parse_datetime, get_pagination_params

bp = Blueprint("workouts", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_workouts():
    patient_ids = get_accessible_patient_ids(current_user)
    query = Workout.query

    if patient_ids is not None:
        query = query.filter(Workout.patient_id.in_(patient_ids))

    pid = request.args.get("patient_id")
    if pid:
        if not can_access_patient_data(current_user, pid):
            return api_error("Forbidden", 403)
        query = query.filter_by(patient_id=pid)

    date_from = parse_datetime(request.args.get("from"))
    date_to = parse_datetime(request.args.get("to"))
    if date_from:
        query = query.filter(Workout.started_at >= date_from)
    if date_to:
        query = query.filter(Workout.started_at <= date_to)

    query = query.order_by(Workout.started_at.desc())
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(
        data=[w.to_dict() for w in items],
        page=page, limit=limit, total=total,
    )


@bp.route("", methods=["POST"])
@jwt_required()
def create_workout():
    data = request.get_json(silent=True) or {}

    if current_user.role == "patient":
        patient_id = str(current_user.id)
    else:
        patient_id = data.get("patient_id")

    if not patient_id:
        return validation_error("patient_id is required")
    if not can_access_patient_data(current_user, patient_id):
        return api_error("Forbidden", 403)

    started_at = parse_datetime(data.get("started_at"))
    if not started_at:
        return validation_error("Valid started_at datetime is required", "started_at")

    workout = Workout(
        patient_id=patient_id,
        started_at=started_at,
        ended_at=parse_datetime(data.get("ended_at")),
        notes=data.get("notes"),
    )
    db.session.add(workout)

    # Add items if provided
    for idx, item_data in enumerate(data.get("items", [])):
        exercise_id = item_data.get("exercise_id")
        if not exercise_id:
            continue
        item = WorkoutItem(
            workout_id=workout.id,
            exercise_id=exercise_id,
            sort_order=item_data.get("sort_order", idx),
            duration_seconds=item_data.get("duration_seconds"),
            sets=item_data.get("sets"),
            reps=item_data.get("reps"),
            weight_kg=item_data.get("weight_kg"),
            notes=item_data.get("notes"),
        )
        db.session.add(item)

    db.session.commit()
    return jsonify(data=workout.to_dict()), 201


@bp.route("/<uuid:workout_id>", methods=["GET"])
@jwt_required()
def get_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return api_error("Workout not found", 404)
    if not can_access_patient_data(current_user, workout.patient_id):
        return api_error("Forbidden", 403)
    return jsonify(data=workout.to_dict())


@bp.route("/<uuid:workout_id>", methods=["PATCH"])
@jwt_required()
def update_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return api_error("Workout not found", 404)
    if not can_access_patient_data(current_user, workout.patient_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    if "started_at" in data:
        dt = parse_datetime(data["started_at"])
        if dt:
            workout.started_at = dt
    if "ended_at" in data:
        workout.ended_at = parse_datetime(data["ended_at"])
    if "notes" in data:
        workout.notes = data["notes"]

    # Replace items if provided
    if "items" in data:
        WorkoutItem.query.filter_by(workout_id=workout.id).delete()
        for idx, item_data in enumerate(data["items"]):
            exercise_id = item_data.get("exercise_id")
            if not exercise_id:
                continue
            item = WorkoutItem(
                workout_id=workout.id,
                exercise_id=exercise_id,
                sort_order=item_data.get("sort_order", idx),
                duration_seconds=item_data.get("duration_seconds"),
                sets=item_data.get("sets"),
                reps=item_data.get("reps"),
                weight_kg=item_data.get("weight_kg"),
                notes=item_data.get("notes"),
            )
            db.session.add(item)

    db.session.commit()
    return jsonify(data=workout.to_dict())


@bp.route("/<uuid:workout_id>", methods=["DELETE"])
@jwt_required()
def delete_workout(workout_id):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return api_error("Workout not found", 404)
    if not can_access_patient_data(current_user, workout.patient_id):
        return api_error("Forbidden", 403)

    db.session.delete(workout)
    db.session.commit()
    return jsonify(message="Workout deleted")


@bp.route("/<uuid:workout_id>/photos", methods=["POST"])
@jwt_required()
def upload_workout_photo(workout_id):
    workout = db.session.get(Workout, workout_id)
    if not workout:
        return api_error("Workout not found", 404)
    if not can_access_patient_data(current_user, workout.patient_id):
        return api_error("Forbidden", 403)

    file = request.files.get("photo")
    if not file:
        return validation_error("Photo file is required", "photo")

    storage = get_storage()
    result = storage.upload(file, folder="workouts")

    photo = WorkoutPhoto(
        workout_id=workout.id,
        storage_key=result["storage_key"],
        caption=request.form.get("caption"),
        sort_order=int(request.form.get("sort_order", 0)),
    )
    db.session.add(photo)
    db.session.commit()
    return jsonify(data=photo.to_dict()), 201
