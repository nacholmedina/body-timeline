import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class ExerciseRequest(db.Model):
    """User requests for new exercises to be added to the catalog."""
    __tablename__ = "exercise_requests"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    requested_by = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(
        db.Enum("cardio", "strength", "sports", "flexibility", "general",
                name="exercise_category", create_type=False),
        nullable=False,
        default="general",
    )
    description = db.Column(db.Text, nullable=True)

    # JSON array of suggested measurement types
    suggested_measurements = db.Column(db.Text, nullable=True)

    status = db.Column(
        db.Enum("pending", "approved", "rejected", name="exercise_request_status"),
        nullable=False,
        default="pending",
        index=True,
    )
    reviewed_by = db.Column(GUID, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)

    # If approved, link to the created exercise
    created_exercise_id = db.Column(
        GUID, db.ForeignKey("exercise_definitions.id"), nullable=True
    )

    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    requester = db.relationship("User", foreign_keys=[requested_by])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    created_exercise = db.relationship("ExerciseDefinition", foreign_keys=[created_exercise_id])

    __table_args__ = (
        db.Index("ix_exercise_requests_status_date", "status", "created_at"),
    )

    def get_suggested_measurements(self):
        """Parse suggested measurements from JSON string."""
        if not self.suggested_measurements:
            return []
        try:
            import json
            return json.loads(self.suggested_measurements)
        except Exception:
            return []

    def set_suggested_measurements(self, measurements):
        """Set suggested measurements as JSON string."""
        import json
        if measurements is None or measurements == []:
            self.suggested_measurements = None
        else:
            self.suggested_measurements = json.dumps(measurements)

    def to_dict(self):
        return {
            "id": str(self.id),
            "requested_by": str(self.requested_by),
            "requester_name": f"{self.requester.first_name} {self.requester.last_name}" if self.requester else None,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "suggested_measurements": self.get_suggested_measurements(),
            "status": self.status,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewer_name": f"{self.reviewer.first_name} {self.reviewer.last_name}" if self.reviewer else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "rejection_reason": self.rejection_reason,
            "created_exercise_id": str(self.created_exercise_id) if self.created_exercise_id else None,
            "created_at": self.created_at.isoformat(),
        }
