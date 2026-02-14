from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models.user import User, ProfessionalPatient


def get_current_user() -> User | None:
    uid = get_jwt_identity()
    if uid is None:
        return None
    return db.session.get(User, uid)


def roles_required(*roles):
    """Decorator: restrict access to specific roles."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if user is None or user.role not in roles:
                return jsonify(error="Forbidden", message="Insufficient permissions"), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def is_assigned_professional(professional_id, patient_id) -> bool:
    """Check if a professional is assigned to a patient."""
    return db.session.query(
        ProfessionalPatient.query.filter_by(
            professional_id=professional_id,
            patient_id=patient_id,
            is_active=True,
        ).exists()
    ).scalar()


def can_access_patient_data(current_user: User, patient_id: str) -> bool:
    """Check if the current user can access a patient's data."""
    if current_user.role == "devadmin":
        return True
    if current_user.role == "patient":
        return str(current_user.id) == str(patient_id)
    if current_user.role == "professional":
        return is_assigned_professional(current_user.id, patient_id)
    return False


def can_modify_patient_data(current_user: User, patient_id: str) -> bool:
    """Check if the current user can modify a patient's data."""
    return can_access_patient_data(current_user, patient_id)


def get_accessible_patient_ids(current_user: User) -> list[str] | None:
    """Return list of patient IDs accessible to the user, or None for 'all'."""
    if current_user.role == "devadmin":
        return None  # all patients
    if current_user.role == "patient":
        return [str(current_user.id)]
    if current_user.role == "professional":
        assignments = ProfessionalPatient.query.filter_by(
            professional_id=current_user.id, is_active=True
        ).all()
        return [str(a.patient_id) for a in assignments]
    return []
