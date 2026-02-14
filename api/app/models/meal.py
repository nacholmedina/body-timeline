import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class Meal(db.Model):
    __tablename__ = "meals"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    description = db.Column(db.Text, nullable=False)
    eaten_at = db.Column(db.DateTime(timezone=True), nullable=False)
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

    patient = db.relationship("User", back_populates="meals")
    photos = db.relationship("MealPhoto", back_populates="meal", cascade="all, delete-orphan", order_by="MealPhoto.sort_order")

    __table_args__ = (db.Index("ix_meals_patient_eaten", "patient_id", "eaten_at"),)

    def to_dict(self, include_photos=True):
        data = {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "description": self.description,
            "eaten_at": self.eaten_at.isoformat(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
        if include_photos:
            data["photos"] = [p.to_dict() for p in self.photos]
        return data


class MealPhoto(db.Model):
    __tablename__ = "meal_photos"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    meal_id = db.Column(
        GUID, db.ForeignKey("meals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_key = db.Column(db.String(500), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    meal = db.relationship("Meal", back_populates="photos")

    def to_dict(self):
        from app.services.storage import get_storage
        return {
            "id": str(self.id),
            "meal_id": str(self.meal_id),
            "storage_key": self.storage_key,
            "url": get_storage().get_url(self.storage_key),
            "caption": self.caption,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat(),
        }
