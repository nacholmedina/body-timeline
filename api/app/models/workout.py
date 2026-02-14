import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class Workout(db.Model):
    __tablename__ = "workouts"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    started_at = db.Column(db.DateTime(timezone=True), nullable=False)
    ended_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

    patient = db.relationship("User", back_populates="workouts")
    items = db.relationship(
        "WorkoutItem", back_populates="workout", cascade="all, delete-orphan",
        order_by="WorkoutItem.sort_order",
    )
    photos = db.relationship(
        "WorkoutPhoto", back_populates="workout", cascade="all, delete-orphan",
        order_by="WorkoutPhoto.sort_order",
    )

    __table_args__ = (db.Index("ix_workouts_patient_started", "patient_id", "started_at"),)

    def to_dict(self, include_items=True, include_photos=True):
        data = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_items:
            data["items"] = [i.to_dict() for i in self.items]
        if include_photos:
            data["photos"] = [p.to_dict() for p in self.photos]
        return data


class WorkoutItem(db.Model):
    __tablename__ = "workout_items"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    workout_id = db.Column(
        GUID, db.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    exercise_id = db.Column(
        GUID, db.ForeignKey("exercises.id"), nullable=False
    )
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    duration_seconds = db.Column(db.Integer, nullable=True)
    sets = db.Column(db.Integer, nullable=True)
    reps = db.Column(db.Integer, nullable=True)
    weight_kg = db.Column(db.Numeric(6, 2), nullable=True)
    notes = db.Column(db.Text, nullable=True)

    workout = db.relationship("Workout", back_populates="items")
    exercise = db.relationship("Exercise")

    def to_dict(self):
        return {
            "id": str(self.id),
            "workout_id": str(self.workout_id),
            "exercise_id": str(self.exercise_id),
            "exercise_name": self.exercise.name if self.exercise else None,
            "sort_order": self.sort_order,
            "duration_seconds": self.duration_seconds,
            "sets": self.sets,
            "reps": self.reps,
            "weight_kg": float(self.weight_kg) if self.weight_kg else None,
            "notes": self.notes,
        }


class WorkoutPhoto(db.Model):
    __tablename__ = "workout_photos"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    workout_id = db.Column(
        GUID, db.ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_key = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    workout = db.relationship("Workout", back_populates="photos")

    def to_dict(self):
        from app.services.storage import get_storage
        return {
            "id": str(self.id),
            "workout_id": str(self.workout_id),
            "storage_key": self.storage_key,
            "url": get_storage().get_url(self.storage_key),
            "caption": self.caption,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat(),
        }
