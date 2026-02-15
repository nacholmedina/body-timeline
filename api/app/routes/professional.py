from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from sqlalchemy import func

from app.extensions import db
from app.models.user import User, ProfessionalPatient
from app.models.patient_invitation import PatientInvitation
from app.models.notification import Notification, NotificationRecipient
from app.models.meal import Meal
from app.models.weigh_in import WeighIn
# Old workout model - commented out after migration to new exercise tracking
# from app.models.workout import Workout
from app.services.rbac import roles_required, get_accessible_patient_ids
from app.utils.errors import validation_error, api_error
from app.utils.validators import validate_email

bp = Blueprint("professional", __name__)


@bp.route("/patients", methods=["GET"])
@jwt_required()
@roles_required("professional", "devadmin")
def list_patients():
    """List all assigned patients with summary stats"""
    patient_ids = get_accessible_patient_ids(current_user)

    if patient_ids is None:
        # Devadmin sees all patients
        query = User.query.filter_by(role="patient")
    else:
        # Professional sees only assigned patients
        query = User.query.filter(User.id.in_(patient_ids))

    patients = query.order_by(User.first_name).all()

    # Enrich with stats
    result = []
    for patient in patients:
        # Get latest weight
        latest_weight = WeighIn.query.filter_by(patient_id=patient.id).order_by(WeighIn.recorded_at.desc()).first()

        # Count totals
        meal_count = Meal.query.filter_by(patient_id=patient.id).count()
        # Old workout count - will be replaced with exercise logs
        workout_count = 0  # Workout.query.filter_by(patient_id=patient.id).count()

        patient_data = {
            "id": str(patient.id),
            "email": patient.email,
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "gender": patient.gender,
            "profile": patient.profile.to_dict() if patient.profile else None,
            "latest_weight": latest_weight.weight_kg if latest_weight else None,
            "total_meals": meal_count,
            "total_workouts": workout_count,
        }
        result.append(patient_data)

    return jsonify(data=result)


@bp.route("/patients/<uuid:patient_id>", methods=["GET"])
@jwt_required()
@roles_required("professional", "devadmin")
def get_patient(patient_id):
    """Get detailed patient profile"""
    from app.services.rbac import can_access_patient_data

    if not can_access_patient_data(current_user, str(patient_id)):
        return api_error("No access to this patient", 403)

    patient = db.session.get(User, patient_id)
    if not patient:
        return api_error("Patient not found", 404)

    # Get weight stats
    weights = WeighIn.query.filter_by(patient_id=patient.id).order_by(WeighIn.recorded_at).all()
    initial_weight = weights[0] if weights else None
    current_weight = weights[-1] if weights else None

    data = {
        "id": str(patient.id),
        "email": patient.email,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "gender": patient.gender,
        "profile": patient.profile.to_dict() if patient.profile else None,
        "weight_stats": {
            "initial_weight": initial_weight.weight_kg if initial_weight else None,
            "initial_date": initial_weight.recorded_at.isoformat() if initial_weight else None,
            "current_weight": current_weight.weight_kg if current_weight else None,
            "current_date": current_weight.recorded_at.isoformat() if current_weight else None,
        },
        "total_meals": Meal.query.filter_by(patient_id=patient.id).count(),
        "total_workouts": 0,  # Workout.query.filter_by(patient_id=patient.id).count() - migrated to exercise logs
    }

    return jsonify(data)


@bp.route("/invitations", methods=["POST"])
@jwt_required()
@roles_required("professional", "devadmin")
def send_invitation():
    """Send invitation to patient by email"""
    data = request.get_json(silent=True) or {}
    email = (data.get("patient_email") or data.get("email") or "").strip().lower()

    if not email:
        return validation_error("Email is required", "patient_email")

    if not validate_email(email):
        return validation_error("Invalid email format", "email")

    # Check if user exists
    user = User.query.filter_by(email=email).first()
    if not user:
        return api_error("User not found. Ask patient to register first.", 404)

    if user.role != "patient":
        return api_error("User is not a patient", 400)

    # Check if already assigned
    existing = ProfessionalPatient.query.filter_by(
        professional_id=current_user.id,
        patient_id=user.id,
        is_active=True
    ).first()

    if existing:
        return api_error("Patient already assigned", 400)

    # Check if pending invitation exists
    pending = PatientInvitation.query.filter_by(
        professional_id=current_user.id,
        patient_email=email,
        status="pending"
    ).first()

    if pending:
        return api_error("Invitation already sent to this patient", 400)

    # Create notification (type key for frontend i18n)
    notification = Notification(
        author_id=current_user.id,
        title="professional_invitation",
        body="",
    )
    db.session.add(notification)
    db.session.flush()

    recipient = NotificationRecipient(
        notification_id=notification.id,
        patient_id=user.id,
    )
    db.session.add(recipient)

    # Create invitation
    invitation = PatientInvitation(
        professional_id=current_user.id,
        patient_email=email,
        status="pending",
        notification_id=notification.id,
    )
    db.session.add(invitation)
    db.session.commit()

    return jsonify(data=invitation.to_dict()), 201


@bp.route("/invitations", methods=["GET"])
@jwt_required()
@roles_required("professional", "devadmin")
def list_invitations():
    """List invitations sent by this professional"""
    invitations = PatientInvitation.query.filter_by(
        professional_id=current_user.id
    ).order_by(PatientInvitation.created_at.desc()).all()

    return jsonify(data=[i.to_dict() for i in invitations])
