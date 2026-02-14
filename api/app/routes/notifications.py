from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.notification import Notification, NotificationRecipient
from app.services.rbac import get_accessible_patient_ids
from app.utils.errors import validation_error, api_error
from app.utils.validators import get_pagination_params

bp = Blueprint("notifications", __name__)


@bp.route("", methods=["GET"])
@jwt_required()
def list_notifications():
    page, limit, offset = get_pagination_params(request.args)

    if current_user.role == "patient":
        # Patient sees notifications sent to them
        query = (
            db.session.query(Notification)
            .join(NotificationRecipient)
            .filter(NotificationRecipient.patient_id == current_user.id)
            .order_by(Notification.created_at.desc())
        )
    elif current_user.role == "professional":
        # Professional sees notifications they authored
        query = Notification.query.filter_by(author_id=current_user.id).order_by(
            Notification.created_at.desc()
        )
    else:
        # devadmin sees all
        query = Notification.query.order_by(Notification.created_at.desc())

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    results = []
    for n in items:
        data = n.to_dict(include_recipients=current_user.role != "patient")
        if current_user.role == "patient":
            recip = NotificationRecipient.query.filter_by(
                notification_id=n.id, patient_id=current_user.id
            ).first()
            if recip:
                data["is_read"] = recip.is_read
                data["read_at"] = recip.read_at.isoformat() if recip.read_at else None
        results.append(data)

    return jsonify(data=results, page=page, limit=limit, total=total)


@bp.route("", methods=["POST"])
@jwt_required()
def create_notification():
    if current_user.role not in ("professional", "devadmin"):
        return api_error("Only professionals and admins can create notifications", 403)

    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    body = (data.get("body") or "").strip()
    patient_ids = data.get("patient_ids", [])

    if not title:
        return validation_error("Title is required", "title")
    if not body:
        return validation_error("Body is required", "body")
    if not patient_ids:
        return validation_error("At least one patient_id is required", "patient_ids")

    # Validate access to patients
    accessible = get_accessible_patient_ids(current_user)
    if accessible is not None:
        for pid in patient_ids:
            if str(pid) not in accessible:
                return api_error(f"No access to patient {pid}", 403)

    notification = Notification(
        author_id=current_user.id,
        title=title,
        body=body,
    )
    db.session.add(notification)
    db.session.flush()

    for pid in patient_ids:
        recipient = NotificationRecipient(
            notification_id=notification.id,
            patient_id=pid,
        )
        db.session.add(recipient)

    db.session.commit()
    return jsonify(data=notification.to_dict(include_recipients=True)), 201


@bp.route("/<uuid:notification_id>/read", methods=["POST"])
@jwt_required()
def mark_read(notification_id):
    if current_user.role != "patient":
        return api_error("Only patients can mark notifications as read", 403)

    recip = NotificationRecipient.query.filter_by(
        notification_id=notification_id,
        patient_id=current_user.id,
    ).first()

    if not recip:
        return api_error("Notification not found", 404)

    recip.is_read = True
    recip.read_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(message="Marked as read")


@bp.route("/unread-count", methods=["GET"])
@jwt_required()
def unread_count():
    if current_user.role != "patient":
        return jsonify(count=0)

    count = NotificationRecipient.query.filter_by(
        patient_id=current_user.id, is_read=False
    ).count()
    return jsonify(count=count)
