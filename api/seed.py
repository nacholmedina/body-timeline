"""Seed script: creates a devadmin user and sample data."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db
from app.models.user import User, Profile


def seed():
    app = create_app()
    with app.app_context():
        # Check if devadmin already exists
        admin = User.query.filter_by(email="admin@wellvio.app").first()
        if admin:
            print("Devadmin already exists, skipping seed.")
            return

        # Create devadmin
        admin = User(
            email="admin@wellvio.app",
            first_name="Admin",
            last_name="Wellvio",
            role="devadmin",
        )
        admin.set_password("Admin123!")
        db.session.add(admin)

        # Create a sample professional
        pro = User(
            email="professional@wellvio.app",
            first_name="Dr. Sarah",
            last_name="Johnson",
            role="professional",
        )
        pro.set_password("Professional123!")
        db.session.add(pro)

        # Create a sample patient
        patient = User(
            email="patient@wellvio.app",
            first_name="John",
            last_name="Doe",
            role="patient",
        )
        patient.set_password("Patient123!")
        db.session.add(patient)

        # Flush to generate UUIDs before creating related records
        db.session.flush()

        db.session.add(Profile(user_id=admin.id))
        db.session.add(Profile(user_id=pro.id))
        db.session.add(Profile(user_id=patient.id))

        # Assign professional to patient
        from app.models.user import ProfessionalPatient
        assignment = ProfessionalPatient(
            professional_id=pro.id, patient_id=patient.id
        )
        db.session.add(assignment)

        db.session.commit()
        print("Seed complete!")
        print(f"  Devadmin:      admin@wellvio.app / Admin123!")
        print(f"  Professional:  professional@wellvio.app / Professional123!")
        print(f"  Patient:       patient@wellvio.app / Patient123!")


if __name__ == "__main__":
    seed()
