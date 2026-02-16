from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.appointment import Appointment
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.utils.errors import validation_error, api_error
from app.utils.validators import parse_datetime, get_pagination_params

bp = Blueprint("appointments", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_appointments():
    patient_ids = get_accessible_patient_ids(current_user)
    query = Appointment.query

    if current_user.role == "professional":
        query = query.filter_by(professional_id=current_user.id)
    elif patient_ids is not None:
        query = query.filter(Appointment.patient_id.in_(patient_ids))

    pid = request.args.get("patient_id")
    if pid:
        if not can_access_patient_data(current_user, pid):
            return api_error("Forbidden", 403)
        query = query.filter_by(patient_id=pid)

    status = request.args.get("status")
    if status in ("scheduled", "completed", "cancelled"):
        query = query.filter_by(status=status)

    upcoming = request.args.get("upcoming")
    if upcoming == "true":
        from datetime import datetime, timezone
        query = query.filter(
            Appointment.scheduled_at >= datetime.now(timezone.utc),
            Appointment.status == "scheduled",
        )

    query = query.order_by(Appointment.scheduled_at.asc())
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[a.to_dict() for a in items], page=page, limit=limit, total=total)


@bp.route("", methods=["POST"])
@jwt_required()
def create_appointment():
    if current_user.role not in ("professional", "devadmin"):
        return api_error("Only professionals can create appointments", 403)

    data = request.get_json(silent=True) or {}
    patient_id = data.get("patient_id")

    # patient_id is optional - allows appointments with non-registered patients
    if patient_id and not can_access_patient_data(current_user, patient_id):
        return api_error("Forbidden", 403)

    scheduled_at = parse_datetime(data.get("scheduled_at"))
    if not scheduled_at:
        return validation_error("Valid scheduled_at datetime is required", "scheduled_at")

    title = (data.get("title") or "").strip()
    if not title:
        return validation_error("Title is required", "title")

    professional_id = str(current_user.id) if current_user.role == "professional" else data.get("professional_id", str(current_user.id))

    appointment = Appointment(
        patient_id=patient_id,
        professional_id=professional_id,
        scheduled_at=scheduled_at,
        duration_minutes=data.get("duration_minutes", 30),
        title=title,
        notes=data.get("notes"),
    )
    db.session.add(appointment)
    db.session.commit()
    return jsonify(data=appointment.to_dict()), 201


@bp.route("/<uuid:appointment_id>", methods=["GET"])
@jwt_required()
def get_appointment(appointment_id):
    appt = db.session.get(Appointment, appointment_id)
    if not appt:
        return api_error("Appointment not found", 404)
    # Check access: if has patient_id, verify access; if no patient_id, check professional ownership
    if appt.patient_id and not can_access_patient_data(current_user, appt.patient_id):
        return api_error("Forbidden", 403)
    if not appt.patient_id and current_user.role == "professional" and str(current_user.id) != str(appt.professional_id):
        return api_error("Forbidden", 403)
    return jsonify(data=appt.to_dict())


@bp.route("/<uuid:appointment_id>", methods=["PATCH"])
@jwt_required()
def update_appointment(appointment_id):
    appt = db.session.get(Appointment, appointment_id)
    if not appt:
        return api_error("Appointment not found", 404)

    if current_user.role == "patient":
        return api_error("Patients cannot modify appointments", 403)
    if current_user.role == "professional" and str(current_user.id) != str(appt.professional_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    if "scheduled_at" in data:
        dt = parse_datetime(data["scheduled_at"])
        if dt:
            appt.scheduled_at = dt
    if "duration_minutes" in data:
        appt.duration_minutes = int(data["duration_minutes"])
    if "title" in data:
        appt.title = data["title"].strip()
    if "notes" in data:
        appt.notes = data["notes"]
    if "status" in data and data["status"] in ("scheduled", "completed", "cancelled"):
        appt.status = data["status"]

    db.session.commit()
    return jsonify(data=appt.to_dict())


@bp.route("/<uuid:appointment_id>", methods=["DELETE"])
@jwt_required()
def delete_appointment(appointment_id):
    appt = db.session.get(Appointment, appointment_id)
    if not appt:
        return api_error("Appointment not found", 404)

    if current_user.role == "patient":
        return api_error("Patients cannot delete appointments", 403)
    if current_user.role == "professional" and str(current_user.id) != str(appt.professional_id):
        return api_error("Forbidden", 403)

    db.session.delete(appt)
    db.session.commit()
    return jsonify(message="Appointment deleted")
