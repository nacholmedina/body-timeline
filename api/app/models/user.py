import uuid
from datetime import datetime, timezone

from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db, GUID


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(
        db.Enum("devadmin", "professional", "patient", name="user_role"),
        nullable=False,
        default="patient",
    )
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(20), nullable=True)  # male, female, other
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

    profile = db.relationship("Profile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    meals = db.relationship("Meal", back_populates="patient", cascade="all, delete-orphan")
    weigh_ins = db.relationship("WeighIn", back_populates="patient", cascade="all, delete-orphan")
    goals = db.relationship("Goal", back_populates="patient", cascade="all, delete-orphan")
    # Old workout tracking - migrated to exercise logs
    # workouts = db.relationship("Workout", back_populates="patient", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self, include_profile=False):
        data = {
            "id": str(self.id),
            "email": self.email,
            "role": self.role,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "gender": self.gender,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }
        if include_profile and self.profile:
            data["profile"] = self.profile.to_dict()
        return data


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(GUID, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    avatar_storage_key = db.Column(db.String(500), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(30), nullable=True, unique=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    height_cm = db.Column(db.Numeric(5, 1), nullable=True)
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

    user = db.relationship("User", back_populates="profile")

    def to_dict(self):
        from app.services.storage import get_storage
        avatar_url = None
        if self.avatar_storage_key:
            try:
                avatar_url = get_storage().get_url(self.avatar_storage_key)
            except Exception:
                pass

        return {
            "id": str(self.id),
            "bio": self.bio,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "height_cm": float(self.height_cm) if self.height_cm else None,
            "avatar_storage_key": self.avatar_storage_key,
            "avatar_url": avatar_url,
        }


class ProfessionalPatient(db.Model):
    __tablename__ = "professional_patients"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    professional_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    professional = db.relationship("User", foreign_keys=[professional_id])
    patient = db.relationship("User", foreign_keys=[patient_id])

    __table_args__ = (
        db.UniqueConstraint("professional_id", "patient_id", name="uq_professional_patient"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "professional_id": str(self.professional_id),
            "patient_id": str(self.patient_id),
            "assigned_at": self.assigned_at.isoformat(),
            "is_active": self.is_active,
        }
