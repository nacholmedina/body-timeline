from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.user import ProfessionalPatient
from app.models.patient_invitation import PatientInvitation
from app.models.notification import Notification, NotificationRecipient
from app.utils.errors import api_error

bp = Blueprint("invitations", __name__)


@bp.route("/pending", methods=["GET"])
@jwt_required()
def list_pending():
    """List pending invitations for current patient"""
    if current_user.role != "patient":
        return jsonify(data=[])

    invitations = PatientInvitation.query.filter_by(
        patient_email=current_user.email,
        status="pending"
    ).order_by(PatientInvitation.created_at.desc()).all()

    return jsonify(data=[i.to_dict() for i in invitations])


@bp.route("/<uuid:invitation_id>/accept", methods=["POST"])
@jwt_required()
def accept_invitation(invitation_id):
    """Patient accepts invitation"""
    if current_user.role != "patient":
        return api_error("Only patients can accept invitations", 403)

    invitation = db.session.get(PatientInvitation, invitation_id)
    if not invitation:
        return api_error("Invitation not found", 404)

    if invitation.patient_email != current_user.email:
        return api_error("This invitation is not for you", 403)

    if invitation.status != "pending":
        return api_error(f"Invitation already {invitation.status}", 400)

    # Check if patient has existing professional
    old_assignment = ProfessionalPatient.query.filter_by(
        patient_id=current_user.id,
        is_active=True
    ).first()

    if old_assignment:
        # Soft delete old assignment
        old_assignment.is_active = False

        # Notify old professional
        notification = Notification(
            author_id=current_user.id,
            title="Patient Assignment Removed",
            body=f"{current_user.first_name} {current_user.last_name} has accepted an invitation from another professional and is no longer your patient.",
        )
        db.session.add(notification)
        db.session.flush()

        recipient = NotificationRecipient(
            notification_id=notification.id,
            patient_id=old_assignment.professional_id,
        )
        db.session.add(recipient)

    # Check if assignment already exists (but inactive)
    existing = ProfessionalPatient.query.filter_by(
        professional_id=invitation.professional_id,
        patient_id=current_user.id
    ).first()

    if existing:
        # Reactivate
        existing.is_active = True
        existing.assigned_at = datetime.now(timezone.utc)
    else:
        # Create new assignment
        assignment = ProfessionalPatient(
            professional_id=invitation.professional_id,
            patient_id=current_user.id,
            is_active=True,
        )
        db.session.add(assignment)

    # Update invitation
    invitation.status = "accepted"
    invitation.responded_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify(message="Invitation accepted", data=invitation.to_dict())


@bp.route("/<uuid:invitation_id>/reject", methods=["POST"])
@jwt_required()
def reject_invitation(invitation_id):
    """Patient rejects invitation"""
    if current_user.role != "patient":
        return api_error("Only patients can reject invitations", 403)

    invitation = db.session.get(PatientInvitation, invitation_id)
    if not invitation:
        return api_error("Invitation not found", 404)

    if invitation.patient_email != current_user.email:
        return api_error("This invitation is not for you", 403)

    if invitation.status != "pending":
        return api_error(f"Invitation already {invitation.status}", 400)

    invitation.status = "rejected"
    invitation.responded_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(message="Invitation rejected", data=invitation.to_dict())
