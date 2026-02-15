import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class MealComment(db.Model):
    __tablename__ = "meal_comments"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    meal_id = db.Column(
        GUID, db.ForeignKey("meals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professional_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    comment = db.Column(db.Text, nullable=False)
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

    meal = db.relationship("Meal", back_populates="comments")
    professional = db.relationship("User", foreign_keys=[professional_id])

    __table_args__ = (db.Index("ix_meal_comments_meal_created", "meal_id", "created_at"),)

    def to_dict(self):
        return {
            "id": str(self.id),
            "meal_id": str(self.meal_id),
            "professional_id": str(self.professional_id),
            "professional_name": (
                f"{self.professional.first_name} {self.professional.last_name}"
                if self.professional
                else None
            ),
            "comment": self.comment,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
