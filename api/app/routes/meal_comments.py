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
@roles_required("professional", "devadmin")
def create_comment(meal_id):
    """Add comment to meal (professionals only)"""
    meal = db.session.get(Meal, meal_id)
    if not meal:
        return api_error("Meal not found", 404)

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

    # Create notification for patient
    notification = Notification(
        author_id=current_user.id,
        title=f"{current_user.first_name} {current_user.last_name} commented on your meal",
        body=f"Your professional has commented on your meal: {comment_text[:100]}{'...' if len(comment_text) > 100 else ''}",
    )
    db.session.add(notification)
    db.session.flush()

    recipient = NotificationRecipient(
        notification_id=notification.id,
        patient_id=meal.patient_id,
    )
    db.session.add(recipient)
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
