from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.meal import Meal
from app.models.meal_comment import MealComment
from app.models.notification import Notification, NotificationRecipient
from app.services.rbac import roles_required, can_access_patient_data
from app.utils.errors import validation_error, api_error

bp = Blueprint("meal_comments", __name__)


@bp.route("/<uuid:meal_id>/comments", methods=["GET"])
@jwt_required()
def list_comments(meal_id):
    """List comments on a meal"""
    meal = db.session.get(Meal, meal_id)
    if not meal:
        return api_error("Meal not found", 404)

    if not can_access_patient_data(current_user, str(meal.patient_id)):
        return api_error("No access to this meal", 403)

    comments = MealComment.query.filter_by(meal_id=meal_id).order_by(MealComment.created_at).all()
    return jsonify(data=[c.to_dict() for c in comments])


@bp.route("/<uuid:meal_id>/comments", methods=["POST"])
@jwt_required()
def create_comment(meal_id):
    """Add comment to meal (professionals, or patients replying to existing thread)"""
    meal = db.session.get(Meal, meal_id)
    if not meal:
        return api_error("Meal not found", 404)

    if current_user.role == "patient":
        # Patients can only reply on their own meals when a professional has commented
        if str(meal.patient_id) != str(current_user.id):
            return api_error("Forbidden", 403)
        has_professional_comment = MealComment.query.filter(
            MealComment.meal_id == meal_id,
            MealComment.professional_id != current_user.id,
        ).first()
        if not has_professional_comment:
            return api_error("You can only reply after a professional comments", 403)
    else:
        if current_user.role not in ("professional", "devadmin"):
            return api_error("Forbidden", 403)
        if not can_access_patient_data(current_user, str(meal.patient_id)):
            return api_error("No access to this meal", 403)

    data = request.get_json(silent=True) or {}
    comment_text = (data.get("comment") or "").strip()

    if not comment_text:
        return validation_error("Comment is required", "comment")

    comment = MealComment(
        meal_id=meal_id,
        professional_id=current_user.id,
        comment=comment_text,
    )
    db.session.add(comment)
    db.session.flush()

    preview = comment_text[:100] + ("..." if len(comment_text) > 100 else "")

    if current_user.role == "patient":
        # Notify all professionals who commented on this meal
        pro_ids = (
            db.session.query(MealComment.professional_id)
            .filter(
                MealComment.meal_id == meal_id,
                MealComment.professional_id != current_user.id,
            )
            .distinct()
            .all()
        )
        if pro_ids:
            notification = Notification(
                author_id=current_user.id,
                title="meal_reply",
                body=preview,
            )
            db.session.add(notification)
            db.session.flush()
            for (pid,) in pro_ids:
                db.session.add(NotificationRecipient(
                    notification_id=notification.id,
                    patient_id=pid,
                ))
    else:
        # Professional commenting → notify patient
        notification = Notification(
            author_id=current_user.id,
            title="meal_comment",
            body=preview,
        )
        db.session.add(notification)
        db.session.flush()
        db.session.add(NotificationRecipient(
            notification_id=notification.id,
            patient_id=meal.patient_id,
        ))

    db.session.commit()
    return jsonify(data=comment.to_dict()), 201


@bp.route("/<uuid:meal_id>/comments/<uuid:comment_id>", methods=["PATCH"])
@jwt_required()
@roles_required("professional", "devadmin")
def update_comment(meal_id, comment_id):
    """Update own comment"""
    comment = db.session.get(MealComment, comment_id)
    if not comment:
        return api_error("Comment not found", 404)

    if comment.meal_id != meal_id:
        return api_error("Comment does not belong to this meal", 400)

    # Only author can edit (or devadmin)
    if comment.professional_id != current_user.id and current_user.role != "devadmin":
        return api_error("Cannot edit another professional's comment", 403)

    data = request.get_json(silent=True) or {}
    comment_text = (data.get("comment") or "").strip()

    if not comment_text:
        return validation_error("Comment is required", "comment")

    comment.comment = comment_text
    comment.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(data=comment.to_dict())


@bp.route("/<uuid:meal_id>/comments/<uuid:comment_id>", methods=["DELETE"])
@jwt_required()
@roles_required("professional", "devadmin")
def delete_comment(meal_id, comment_id):
    """Delete own comment"""
    comment = db.session.get(MealComment, comment_id)
    if not comment:
        return api_error("Comment not found", 404)

    if comment.meal_id != meal_id:
        return api_error("Comment does not belong to this meal", 400)

    # Only author can delete (or devadmin)
    if comment.professional_id != current_user.id and current_user.role != "devadmin":
        return api_error("Cannot delete another professional's comment", 403)

    db.session.delete(comment)
    db.session.commit()

    return jsonify(message="Comment deleted")
