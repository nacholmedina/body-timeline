import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class ExerciseDefinition(db.Model):
    """Exercise catalog - templates for exercises users can log."""
    __tablename__ = "exercise_definitions"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False, unique=True, index=True)
    category = db.Column(
        db.Enum("cardio", "strength", "sports", "flexibility", "general",
                name="exercise_category"),
        nullable=False,
        default="general",
        index=True,
    )
    description = db.Column(db.Text, nullable=True)

    # JSON array of allowed measurement types: ["duration", "reps", "distance", etc.]
    allowed_measurements = db.Column(db.Text, nullable=True)

    # System exercises are pre-seeded and cannot be deleted
    is_system = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Usage tracking for sorting by popularity
    usage_count = db.Column(db.Integer, default=0, nullable=False)

    # Who created this exercise (null for system exercises)
    created_by = db.Column(GUID, db.ForeignKey("users.id"), nullable=True)

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

    creator = db.relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        db.Index("ix_exercise_defs_category_usage", "category", "is_active", "usage_count"),
    )

    def get_allowed_measurements(self):
        """Parse allowed measurements from JSON string."""
        if not self.allowed_measurements:
            return []
        try:
            import json
            return json.loads(self.allowed_measurements)
        except Exception:
            return []

    def set_allowed_measurements(self, measurements):
        """Set allowed measurements as JSON string."""
        import json
        if measurements is None:
            self.allowed_measurements = None
        else:
            self.allowed_measurements = json.dumps(measurements)

    def increment_usage(self):
        """Increment usage count for popularity tracking."""
        self.usage_count += 1

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "allowed_measurements": self.get_allowed_measurements(),
            "is_system": self.is_system,
            "is_active": self.is_active,
            "usage_count": self.usage_count,
            "created_by": str(self.created_by) if self.created_by else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
