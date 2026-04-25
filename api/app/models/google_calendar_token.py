import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class GoogleCalendarToken(db.Model):
    __tablename__ = "google_calendar_tokens"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text, nullable=False)
    expires_at = db.Column(db.DateTime(timezone=True), nullable=False)
    scope = db.Column(db.Text, nullable=False)
    calendar_id = db.Column(db.String(255), nullable=False, default="primary")
    google_email = db.Column(db.String(255), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user = db.relationship("User", foreign_keys=[user_id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "calendar_id": self.calendar_id,
            "google_email": self.google_email,
            "scope": self.scope,
            "expires_at": self.expires_at.isoformat(),
            "created_at": self.created_at.isoformat(),
        }
