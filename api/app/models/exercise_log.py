import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class ExerciseLog(db.Model):
    """Individual exercise instances logged by patients."""
    __tablename__ = "exercise_logs"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Reference to exercise definition (null for "Other" custom exercises)
    exercise_definition_id = db.Column(
        GUID, db.ForeignKey("exercise_definitions.id"), nullable=True, index=True
    )

    # For "Other" exercise type - custom name and description
    custom_exercise_name = db.Column(db.String(200), nullable=True)
    custom_exercise_description = db.Column(db.Text, nullable=True)

    # JSON object with measurements: {duration: 1800, reps: 10, distance: 5.5, ...}
    # All measurements are optional
    measurements = db.Column(db.Text, nullable=True)

    # When the exercise was performed
    performed_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)

    # Optional notes
    notes = db.Column(db.Text, nullable=True)

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

    patient = db.relationship("User", foreign_keys=[patient_id])
    exercise_definition = db.relationship("ExerciseDefinition", foreign_keys=[exercise_definition_id])
    photos = db.relationship(
        "ExercisePhoto", back_populates="exercise_log", cascade="all, delete-orphan",
        order_by="ExercisePhoto.sort_order",
    )

    __table_args__ = (
        db.Index("ix_exercise_logs_patient_date", "patient_id", "performed_at"),
    )

    def get_measurements(self):
        """Parse measurements from JSON string."""
        if not self.measurements:
            return {}
        try:
            import json
            return json.loads(self.measurements)
        except Exception:
            return {}

    def set_measurements(self, measurements_dict):
        """Set measurements as JSON string."""
        import json
        if measurements_dict is None or measurements_dict == {}:
            self.measurements = None
        else:
            self.measurements = json.dumps(measurements_dict)

    def get_exercise_name(self):
        """Get the exercise name (from definition or custom)."""
        if self.exercise_definition:
            return self.exercise_definition.name
        return self.custom_exercise_name or "Exercise"

    def to_dict(self, include_photos=True):
        data = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "exercise_definition_id": str(self.exercise_definition_id) if self.exercise_definition_id else None,
            "exercise_name": self.get_exercise_name(),
            "exercise_category": self.exercise_definition.category if self.exercise_definition else "general",
            "custom_exercise_name": self.custom_exercise_name,
            "custom_exercise_description": self.custom_exercise_description,
            "measurements": self.get_measurements(),
            "performed_at": self.performed_at.isoformat(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_photos:
            data["photos"] = [p.to_dict() for p in self.photos]
        return data


class ExercisePhoto(db.Model):
    """Photos attached to exercise logs."""
    __tablename__ = "exercise_photos"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    exercise_log_id = db.Column(
        GUID, db.ForeignKey("exercise_logs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_key = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    exercise_log = db.relationship("ExerciseLog", back_populates="photos")

    def to_dict(self):
        from app.services.storage import get_storage
        return {
            "id": str(self.id),
            "exercise_log_id": str(self.exercise_log_id),
            "storage_key": self.storage_key,
            "url": get_storage().get_url(self.storage_key),
            "caption": self.caption,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat(),
        }
