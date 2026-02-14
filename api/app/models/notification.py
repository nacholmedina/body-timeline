import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    author_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    author = db.relationship("User", foreign_keys=[author_id])
    recipients = db.relationship(
        "NotificationRecipient", back_populates="notification",
        cascade="all, delete-orphan",
    )

    def to_dict(self, include_recipients=False):
        data = {
            "id": str(self.id),
            "author_id": str(self.author_id),
            "author_name": f"{self.author.first_name} {self.author.last_name}" if self.author else None,
            "title": self.title,
            "body": self.body,
            "created_at": self.created_at.isoformat(),
        }
        if include_recipients:
            data["recipients"] = [r.to_dict() for r in self.recipients]
        return data


class NotificationRecipient(db.Model):
    __tablename__ = "notification_recipients"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    notification_id = db.Column(
        GUID, db.ForeignKey("notifications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    read_at = db.Column(db.DateTime(timezone=True), nullable=True)

    notification = db.relationship("Notification", back_populates="recipients")
    patient = db.relationship("User", foreign_keys=[patient_id])

    __table_args__ = (
        db.UniqueConstraint("notification_id", "patient_id", name="uq_notification_recipient"),
        db.Index("ix_notif_recip_patient_read", "patient_id", "is_read"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "notification_id": str(self.notification_id),
            "patient_id": str(self.patient_id),
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
        }
