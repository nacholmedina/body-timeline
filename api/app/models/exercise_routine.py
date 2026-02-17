import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class ExerciseRoutine(db.Model):
    """Patient-specific exercise routine templates (e.g., 'Leg Day', 'Morning Routine')."""
    __tablename__ = "exercise_routines"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

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
    items = db.relationship(
        "ExerciseRoutineItem",
        back_populates="routine",
        cascade="all, delete-orphan",
        order_by="ExerciseRoutineItem.sort_order",
    )

    __table_args__ = (
        db.Index("ix_exercise_routines_patient", "patient_id", "is_active"),
    )

    def to_dict(self, include_items=True):
        data = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "name": self.name,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
            data["exercise_count"] = len(self.items)
        return data


class ExerciseRoutineItem(db.Model):
    """Individual exercises within a routine, with optional default measurements."""
    __tablename__ = "exercise_routine_items"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    routine_id = db.Column(
        GUID, db.ForeignKey("exercise_routines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exercise_definition_id = db.Column(
        GUID, db.ForeignKey("exercise_definitions.id"), nullable=False
    )
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    # Optional default measurements as JSON: {"reps": 10, "sets": 3, "weight": 50}
    default_measurements = db.Column(db.Text, nullable=True)

    # Optional notes for this specific exercise in the routine
    notes = db.Column(db.Text, nullable=True)

    routine = db.relationship("ExerciseRoutine", back_populates="items")
    exercise_definition = db.relationship("ExerciseDefinition")

    def get_default_measurements(self):
        """Parse default measurements from JSON string."""
        if not self.default_measurements:
            return {}
        try:
            import json
            return json.loads(self.default_measurements)
        except Exception:
            return {}

    def set_default_measurements(self, measurements_dict):
        """Set default measurements as JSON string."""
        import json
        if measurements_dict is None or measurements_dict == {}:
            self.default_measurements = None
        else:
            self.default_measurements = json.dumps(measurements_dict)

    def to_dict(self):
        return {
            "id": str(self.id),
            "routine_id": str(self.routine_id),
            "exercise_definition_id": str(self.exercise_definition_id),
            "exercise_name": self.exercise_definition.name if self.exercise_definition else None,
            "exercise_category": self.exercise_definition.category if self.exercise_definition else None,
            "allowed_measurements": self.exercise_definition.get_allowed_measurements() if self.exercise_definition else [],
            "sort_order": self.sort_order,
            "default_measurements": self.get_default_measurements(),
            "notes": self.notes,
        }
