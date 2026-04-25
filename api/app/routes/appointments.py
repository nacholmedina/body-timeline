from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.appointment import Appointment
from app.models.notification import Notification, NotificationRecipient
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.services import google_calendar as gcal
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

    # Notify patient when appointment is created
    if patient_id:
        notification = Notification(
            author_id=current_user.id,
            title="appointment_scheduled",
            body=f"{title} - {scheduled_at.strftime('%Y-%m-%d %H:%M')}",
        )
        db.session.add(notification)
        db.session.flush()
        recipient = NotificationRecipient(
            notification_id=notification.id,
            patient_id=patient_id
        )
        db.session.add(recipient)

    db.session.commit()

    event_id = gcal.create_event(appointment)
    if event_id:
        appointment.google_event_id = event_id
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
        # Patients can only cancel their own appointments
        if str(appt.patient_id) != str(current_user.id):
            return api_error("Forbidden", 403)
        data = request.get_json(silent=True) or {}
        if data.get("status") != "cancelled" or len(data) > 1:
            return api_error("Patients can only cancel appointments", 403)
        if appt.status != "scheduled":
            return api_error("Can only cancel scheduled appointments", 400)

        appt.status = "cancelled"

        # Notify professional that patient cancelled
        notif = Notification(
            author_id=current_user.id,
            title="appointment_cancelled_by_patient",
            body=f"{appt.title} - {appt.scheduled_at.strftime('%Y-%m-%d %H:%M')}",
        )
        db.session.add(notif)
        db.session.flush()
        db.session.add(NotificationRecipient(
            notification_id=notif.id,
            patient_id=appt.professional_id,
        ))

        # Also notify the patient (confirmation)
        patient_notif = Notification(
            author_id=current_user.id,
            title="appointment_cancelled",
            body=f"{appt.title} - {appt.scheduled_at.strftime('%Y-%m-%d %H:%M')}",
        )
        db.session.add(patient_notif)
        db.session.flush()
        db.session.add(NotificationRecipient(
            notification_id=patient_notif.id,
            patient_id=current_user.id,
        ))

        db.session.commit()
        if gcal.delete_event(appt):
            appt.google_event_id = None
            db.session.commit()
        return jsonify(data=appt.to_dict())

    if current_user.role == "professional" and str(current_user.id) != str(appt.professional_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    status_changed_to_cancelled = False
    schedule_or_content_changed = False

    if "scheduled_at" in data:
        dt = parse_datetime(data["scheduled_at"])
        if dt:
            appt.scheduled_at = dt
            schedule_or_content_changed = True
    if "duration_minutes" in data:
        appt.duration_minutes = int(data["duration_minutes"])
        schedule_or_content_changed = True
    if "title" in data:
        appt.title = data["title"].strip()
        schedule_or_content_changed = True
    if "notes" in data:
        appt.notes = data["notes"]
        schedule_or_content_changed = True
    if "status" in data and data["status"] in ("scheduled", "completed", "cancelled"):
        if data["status"] == "cancelled" and appt.status != "cancelled":
            status_changed_to_cancelled = True
        appt.status = data["status"]

    # Notify patient when appointment is cancelled by professional
    if status_changed_to_cancelled and appt.patient_id:
        notification = Notification(
            author_id=current_user.id,
            title="appointment_cancelled",
            body=f"{appt.title} - {appt.scheduled_at.strftime('%Y-%m-%d %H:%M')}",
        )
        db.session.add(notification)
        db.session.flush()
        recipient = NotificationRecipient(
            notification_id=notification.id,
            patient_id=appt.patient_id
        )
        db.session.add(recipient)

    db.session.commit()

    if status_changed_to_cancelled:
        if gcal.delete_event(appt):
            appt.google_event_id = None
            db.session.commit()
    elif appt.status == "scheduled" and schedule_or_content_changed and appt.google_event_id:
        gcal.update_event(appt)

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

    # Notify patient when appointment is deleted
    if appt.patient_id:
        notification = Notification(
            author_id=current_user.id,
            title="appointment_deleted",
            body=f"{appt.title} - {appt.scheduled_at.strftime('%Y-%m-%d %H:%M')}",
        )
        db.session.add(notification)
        db.session.flush()
        recipient = NotificationRecipient(
            notification_id=notification.id,
            patient_id=appt.patient_id
        )
        db.session.add(recipient)

    # Best-effort delete the Google Calendar event before removing the row.
    gcal.delete_event(appt)

    db.session.delete(appt)
    db.session.commit()
    return jsonify(message="Appointment deleted")
