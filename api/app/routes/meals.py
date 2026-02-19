from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.meal import Meal, MealPhoto
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.services.storage import get_storage
from app.utils.errors import validation_error, api_error
from app.utils.validators import parse_datetime, get_pagination_params

bp = Blueprint("meals", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_meals():
    patient_ids = get_accessible_patient_ids(current_user)
    query = Meal.query

    if patient_ids is not None:
        query = query.filter(Meal.patient_id.in_(patient_ids))

    # Filters
    pid = request.args.get("patient_id")
    if pid:
        if not can_access_patient_data(current_user, pid):
            return api_error("Forbidden", 403)
        query = query.filter_by(patient_id=pid)

    date_from = parse_datetime(request.args.get("from"))
    date_to = parse_datetime(request.args.get("to"))
    if date_from:
        query = query.filter(Meal.eaten_at >= date_from)
    if date_to:
        query = query.filter(Meal.eaten_at <= date_to)

    query = query.order_by(Meal.eaten_at.desc())
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    meals = query.offset(offset).limit(limit).all()

    return jsonify(
        data=[m.to_dict() for m in meals],
        page=page, limit=limit, total=total,
    )


@bp.route("", methods=["POST"])
@jwt_required()
def create_meal():
    if current_user.role not in ("patient", "devadmin"):
        return api_error("Only patients can create meals", 403)

    data = request.get_json(silent=True) or {}
    patient_id = str(current_user.id) if current_user.role == "patient" else data.get("patient_id")
    if not patient_id:
        return validation_error("patient_id is required")

    if not can_access_patient_data(current_user, patient_id):
        return api_error("Forbidden", 403)

    description = (data.get("description") or "").strip()
    eaten_at = parse_datetime(data.get("eaten_at"))
    if not description:
        return validation_error("Description is required", "description")
    if not eaten_at:
        return validation_error("Valid eaten_at datetime is required", "eaten_at")

    meal = Meal(
        patient_id=patient_id,
        description=description,
        eaten_at=eaten_at,
        notes=data.get("notes"),
    )
    db.session.add(meal)
    db.session.commit()
    return jsonify(data=meal.to_dict()), 201


@bp.route("/<uuid:meal_id>", methods=["GET"])
@jwt_required()
def get_meal(meal_id):
    meal = db.session.get(Meal, meal_id)
    if not meal:
        return api_error("Meal not found", 404)
    if not can_access_patient_data(current_user, meal.patient_id):
        return api_error("Forbidden", 403)
    return jsonify(data=meal.to_dict())


@bp.route("/<uuid:meal_id>", methods=["PATCH"])
@jwt_required()
def update_meal(meal_id):
    meal = db.session.get(Meal, meal_id)
    if not meal:
        return api_error("Meal not found", 404)

    if current_user.role == "patient" and str(current_user.id) != str(meal.patient_id):
        return api_error("Forbidden", 403)
    if current_user.role == "professional":
        return api_error("Professionals cannot modify meals", 403)

    data = request.get_json(silent=True) or {}
    if "description" in data:
        meal.description = data["description"].strip()
    if "eaten_at" in data:
        eaten_at = parse_datetime(data["eaten_at"])
        if eaten_at:
            meal.eaten_at = eaten_at
    if "notes" in data:
        meal.notes = data["notes"]

    db.session.commit()
    return jsonify(data=meal.to_dict())


@bp.route("/<uuid:meal_id>", methods=["DELETE"])
@jwt_required()
def delete_meal(meal_id):
    meal = db.session.get(Meal, meal_id)
    if not meal:
        return api_error("Meal not found", 404)

    if current_user.role == "patient" and str(current_user.id) != str(meal.patient_id):
        return api_error("Forbidden", 403)
    if current_user.role == "professional":
        return api_error("Professionals cannot delete meals", 403)

    db.session.delete(meal)
    db.session.commit()
    return jsonify(message="Meal deleted"), 200


@bp.route("/<uuid:meal_id>/photos", methods=["POST"])
@jwt_required()
def upload_meal_photo(meal_id):
    meal = db.session.get(Meal, meal_id)
    if not meal:
        return api_error("Meal not found", 404)

    if current_user.role == "patient" and str(current_user.id) != str(meal.patient_id):
        return api_error("Forbidden", 403)
    if current_user.role == "professional":
        return api_error("Professionals cannot modify meals", 403)

    if len(meal.photos) >= 3:
        return api_error("Maximum 3 photos per meal", 400)

    file = request.files.get("photo")
    if not file:
        return validation_error("Photo file is required", "photo")

    storage = get_storage()
    result = storage.upload(file, folder="meals")

    photo = MealPhoto(
        meal_id=meal.id,
        storage_key=result["storage_key"],
        caption=request.form.get("caption"),
        sort_order=int(request.form.get("sort_order", 0)),
    )
    db.session.add(photo)
    db.session.commit()

    return jsonify(data=photo.to_dict()), 201


@bp.route("/<uuid:meal_id>/photos/<uuid:photo_id>", methods=["DELETE"])
@jwt_required()
def delete_meal_photo(meal_id, photo_id):
    meal = db.session.get(Meal, meal_id)
    if not meal:
        return api_error("Meal not found", 404)

    if current_user.role == "patient" and str(current_user.id) != str(meal.patient_id):
        return api_error("Forbidden", 403)
    if current_user.role == "professional":
        return api_error("Professionals cannot modify meals", 403)

    photo = db.session.get(MealPhoto, photo_id)
    if not photo or str(photo.meal_id) != str(meal_id):
        return api_error("Photo not found", 404)

    try:
        storage = get_storage()
        storage.delete(photo.storage_key)
    except Exception:
        pass

    db.session.delete(photo)
    db.session.commit()
    return jsonify(message="Photo deleted")
