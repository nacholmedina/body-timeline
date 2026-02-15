import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class PatientInvitation(db.Model):
    __tablename__ = "patient_invitations"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    professional_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_email = db.Column(db.String(255), nullable=False, index=True)
    status = db.Column(
        db.Enum("pending", "accepted", "rejected", name="invitation_status"),
        nullable=False,
        default="pending",
    )
    notification_id = db.Column(
        GUID, db.ForeignKey("notifications.id", ondelete="SET NULL"), nullable=True
    )
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    responded_at = db.Column(db.DateTime(timezone=True), nullable=True)

    professional = db.relationship("User", foreign_keys=[professional_id])
    notification = db.relationship("Notification", foreign_keys=[notification_id])

    __table_args__ = (
        db.Index("ix_patient_inv_email_status", "patient_email", "status"),
        db.Index("ix_patient_inv_prof_status", "professional_id", "status"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "professional_id": str(self.professional_id),
            "professional_name": (
                f"{self.professional.first_name} {self.professional.last_name}"
                if self.professional
                else None
            ),
            "professional_email": self.professional.email if self.professional else None,
            "patient_email": self.patient_email,
            "status": self.status,
            "notification_id": str(self.notification_id) if self.notification_id else None,
            "created_at": self.created_at.isoformat(),
            "responded_at": self.responded_at.isoformat() if self.responded_at else None,
        }
