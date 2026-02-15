from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, current_user, get_jwt,
)

from app.extensions import db
from app.models.user import User, Profile, ProfessionalPatient
from app.services.rbac import roles_required
from app.utils.errors import validation_error, api_error
from app.utils.validators import validate_email, validate_password, get_pagination_params

bp = Blueprint("admin", __name__)


# ── Stats ────────────────────────────────────────────────

@bp.route("/stats", methods=["GET"])
@roles_required("devadmin")
def stats():
    total = User.query.count()
    by_role = {}
    for role in ("devadmin", "professional", "patient"):
        by_role[role] = User.query.filter_by(role=role).count()

    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
    recent = User.query.filter(User.created_at >= thirty_days_ago).count()
    assignments = ProfessionalPatient.query.filter_by(is_active=True).count()

    return jsonify(
        total_users=total,
        users_by_role=by_role,
        recent_registrations=recent,
        total_assignments=assignments,
    )


# ── User management ─────────────────────────────────────

@bp.route("/users", methods=["GET"])
@roles_required("devadmin")
def list_users():
    query = User.query
    role = request.args.get("role")
    if role:
        query = query.filter_by(role=role)

    search = request.args.get("search")
    if search:
        like = f"%{search}%"
        query = query.filter(
            db.or_(User.email.ilike(like), User.first_name.ilike(like), User.last_name.ilike(like))
        )

    query = query.order_by(User.created_at.desc())
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[u.to_dict() for u in items], page=page, limit=limit, total=total)


@bp.route("/users", methods=["POST"])
@roles_required("devadmin")
def create_user():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    role = data.get("role", "patient")

    if not email or not validate_email(email):
        return validation_error("Valid email is required", "email")
    if not validate_password(password):
        return validation_error("Password must be at least 8 characters", "password")
    if not first_name or not last_name:
        return validation_error("First and last name are required")
    if role not in ("devadmin", "professional", "patient"):
        return validation_error("Invalid role", "role")

    if User.query.filter_by(email=email).first():
        return api_error("Email already in use", 409)

    user = User(email=email, first_name=first_name, last_name=last_name, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    db.session.add(Profile(user_id=user.id))
    db.session.commit()

    return jsonify(data=user.to_dict()), 201


@bp.route("/users/<uuid:user_id>/role", methods=["PATCH"])
@roles_required("devadmin")
def change_role(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return api_error("User not found", 404)

    data = request.get_json(silent=True) or {}
    new_role = data.get("role")
    if new_role not in ("devadmin", "professional", "patient"):
        return validation_error("Invalid role")

    user.role = new_role
    db.session.commit()
    return jsonify(data=user.to_dict())


@bp.route("/users/<uuid:user_id>/toggle-active", methods=["POST"])
@roles_required("devadmin")
def toggle_active(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return api_error("User not found", 404)

    user.is_active = not user.is_active
    db.session.commit()
    return jsonify(data=user.to_dict())


# ── Impersonation ────────────────────────────────────────

@bp.route("/impersonate/<uuid:user_id>", methods=["POST"])
@roles_required("devadmin")
def impersonate(user_id):
    target = db.session.get(User, user_id)
    if not target:
        return api_error("User not found", 404)
    if str(target.id) == str(current_user.id):
        return api_error("Cannot impersonate yourself", 400)

    additional_claims = {
        "is_impersonating": True,
        "admin_id": str(current_user.id),
    }
    access_token = create_access_token(
        identity=target, additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(
        identity=target, additional_claims=additional_claims
    )

    from app.routes.auth import _weight_stats, _my_professional
    user_data = target.to_dict(include_profile=True)
    user_data["weight_stats"] = _weight_stats(target.id)
    if target.role == "patient":
        user_data["my_professional"] = _my_professional(target.id)

    return jsonify(
        user=user_data,
        access_token=access_token,
        refresh_token=refresh_token,
    )


@bp.route("/stop-impersonation", methods=["POST"])
@jwt_required()
def stop_impersonation():
    claims = get_jwt()
    admin_id = claims.get("admin_id")
    if not admin_id:
        return api_error("Not impersonating", 400)

    admin = db.session.get(User, admin_id)
    if not admin:
        return api_error("Admin user not found", 404)

    access_token = create_access_token(identity=admin)
    refresh_token = create_refresh_token(identity=admin)

    return jsonify(
        user=admin.to_dict(include_profile=True),
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ── Professional-Patient assignments ──────────────────────

@bp.route("/assignments", methods=["GET"])
@jwt_required()
def list_assignments():
    if current_user.role == "devadmin":
        query = ProfessionalPatient.query
    elif current_user.role == "professional":
        query = ProfessionalPatient.query.filter_by(professional_id=current_user.id)
    else:
        query = ProfessionalPatient.query.filter_by(patient_id=current_user.id)

    items = query.filter_by(is_active=True).all()
    results = []
    for a in items:
        d = a.to_dict()
        pro = a.professional
        pat = a.patient
        d["professional_name"] = f"{pro.first_name} {pro.last_name}" if pro else "Unknown"
        d["patient_name"] = f"{pat.first_name} {pat.last_name}" if pat else "Unknown"
        results.append(d)

    return jsonify(data=results)


@bp.route("/assignments", methods=["POST"])
@roles_required("devadmin")
def create_assignment():
    data = request.get_json(silent=True) or {}
    professional_id = data.get("professional_id")
    patient_id = data.get("patient_id")

    if not professional_id or not patient_id:
        return validation_error("professional_id and patient_id are required")

    professional = db.session.get(User, professional_id)
    if not professional or professional.role != "professional":
        return api_error("Professional not found", 404)

    patient = db.session.get(User, patient_id)
    if not patient or patient.role != "patient":
        return api_error("Patient not found", 404)

    existing = ProfessionalPatient.query.filter_by(
        professional_id=professional_id, patient_id=patient_id
    ).first()

    if existing:
        existing.is_active = True
        db.session.commit()
        return jsonify(data=existing.to_dict())

    assignment = ProfessionalPatient(
        professional_id=professional_id, patient_id=patient_id
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify(data=assignment.to_dict()), 201


@bp.route("/assignments/<uuid:assignment_id>", methods=["DELETE"])
@roles_required("devadmin")
def remove_assignment(assignment_id):
    a = db.session.get(ProfessionalPatient, assignment_id)
    if not a:
        return api_error("Assignment not found", 404)

    a.is_active = False
    db.session.commit()
    return jsonify(message="Assignment deactivated")
