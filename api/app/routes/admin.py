from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.user import User, ProfessionalPatient
from app.services.rbac import roles_required
from app.utils.errors import validation_error, api_error
from app.utils.validators import get_pagination_params

bp = Blueprint("admin", __name__)


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
        d["professional_name"] = f"{a.professional.first_name} {a.professional.last_name}"
        d["patient_name"] = f"{a.patient.first_name} {a.patient.last_name}"
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
