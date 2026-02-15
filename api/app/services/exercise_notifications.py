"""Exercise request notification service."""

from app.extensions import db
from app.models.user import User
from app.models.notification import Notification, NotificationRecipient


def notify_devadmins_new_exercise_request(exercise_request, requester) -> None:
    """
    Notify all active devadmins when a new exercise is requested.

    Args:
        exercise_request: ExerciseRequest model instance
        requester: User who made the request
    """
    # Query all active devadmins
    devadmins = User.query.filter_by(role="devadmin", is_active=True).all()

    if not devadmins:
        return  # No devadmins to notify

    # Create notification
    notification = Notification(
        author_id=requester.id,
        title="exercise_request_created",
        body=f"{requester.first_name} {requester.last_name} requested new exercise: {exercise_request.name}",
    )
    db.session.add(notification)
    db.session.flush()

    # Create notification recipients for each devadmin
    for admin in devadmins:
        recipient = NotificationRecipient(
            notification_id=notification.id,
            patient_id=admin.id,  # Reusing patient_id field for recipient_id
        )
        db.session.add(recipient)


def notify_requester_exercise_reviewed(exercise_request, reviewer, approved: bool) -> None:
    """
    Notify the requester when their exercise request is reviewed.

    Args:
        exercise_request: ExerciseRequest model instance
        reviewer: User who reviewed the request
        approved: Whether the request was approved
    """
    status = "approved" if approved else "rejected"
    notification = Notification(
        author_id=reviewer.id,
        title=f"exercise_request_{status}",
        body=f"Your exercise request '{exercise_request.name}' has been {status}.",
    )
    db.session.add(notification)
    db.session.flush()

    recipient = NotificationRecipient(
        notification_id=notification.id,
        patient_id=exercise_request.requested_by,
    )
    db.session.add(recipient)
