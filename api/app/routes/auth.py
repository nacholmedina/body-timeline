from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, current_user,
)

from app.extensions import db
from app.models.user import User, Profile, ProfessionalPatient
from app.models.weigh_in import WeighIn
from app.utils.errors import validation_error, api_error
from app.utils.validators import validate_email, validate_password


def _weight_stats(user_id):
    """Return initial (oldest) and current (newest) weigh-in for a user."""
    oldest = (
        WeighIn.query
        .filter_by(patient_id=user_id)
        .order_by(WeighIn.recorded_at.asc())
        .first()
    )
    newest = (
        WeighIn.query
        .filter_by(patient_id=user_id)
        .order_by(WeighIn.recorded_at.desc())
        .first()
    )
    return {
        "initial_weight_kg": float(oldest.weight_kg) if oldest else None,
        "initial_weight_date": oldest.recorded_at.isoformat() if oldest else None,
        "current_weight_kg": float(newest.weight_kg) if newest else None,
        "current_weight_date": newest.recorded_at.isoformat() if newest else None,
    }

def _my_professional(user_id):
    """Return the assigned professional's public info for a patient."""
    assignment = (
        ProfessionalPatient.query
        .filter_by(patient_id=user_id, is_active=True)
        .first()
    )
    if not assignment:
        return None
    prof = db.session.get(User, assignment.professional_id)
    if not prof:
        return None
    prof_profile = prof.profile
    return {
        "first_name": prof.first_name,
        "last_name": prof.last_name,
        "email": prof.email,
        "phone": prof_profile.phone if prof_profile else None,
        "bio": prof_profile.bio if prof_profile else None,
    }


bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()

    if not email or not validate_email(email):
        return validation_error("Valid email is required", "email")
    if not first_name or not last_name:
        return validation_error("First name and last name are required")

    pw_err = validate_password(password)
    if pw_err:
        return validation_error(pw_err, "password")

    if User.query.filter_by(email=email).first():
        return api_error("Email already registered", 409)

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role="patient",
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # generate user.id before creating profile

    profile = Profile(user_id=user.id)
    db.session.add(profile)

    db.session.commit()

    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    user_data = user.to_dict(include_profile=True)
    user_data["weight_stats"] = _weight_stats(user.id)

    return jsonify(
        user=user_data,
        access_token=access_token,
        refresh_token=refresh_token,
    ), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return validation_error("Email and password are required")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return api_error("Invalid email or password", 401)

    if not user.is_active:
        return api_error("Account is deactivated", 403)

    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)
    user_data = user.to_dict(include_profile=True)
    user_data["weight_stats"] = _weight_stats(user.id)
    if user.role == "patient":
        user_data["my_professional"] = _my_professional(user.id)

    return jsonify(
        user=user_data,
        access_token=access_token,
        refresh_token=refresh_token,
    )


@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    access_token = create_access_token(identity=get_jwt_identity())
    return jsonify(access_token=access_token)


@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    data = current_user.to_dict(include_profile=True)
    data["weight_stats"] = _weight_stats(current_user.id)
    if current_user.role == "patient":
        data["my_professional"] = _my_professional(current_user.id)
    return jsonify(user=data)


@bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_me():
    data = request.get_json(silent=True) or {}
    user = current_user

    if "first_name" in data:
        fname = (data["first_name"] or "").strip()
        if not fname:
            return validation_error("First name cannot be empty", "first_name")
        user.first_name = fname
    if "last_name" in data:
        lname = (data["last_name"] or "").strip()
        if not lname:
            return validation_error("Last name cannot be empty", "last_name")
        user.last_name = lname

    profile = user.profile
    if not profile:
        profile = Profile(user_id=user.id)
        db.session.add(profile)

    for field in ("bio", "phone", "date_of_birth", "height_cm"):
        if field in data:
            setattr(profile, field, data[field])

    db.session.commit()
    data = user.to_dict(include_profile=True)
    data["weight_stats"] = _weight_stats(user.id)
    if user.role == "patient":
        data["my_professional"] = _my_professional(user.id)
    return jsonify(user=data)
