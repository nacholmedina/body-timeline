"""
One-time migration endpoint - DELETE AFTER USE
"""
from flask import Flask, jsonify
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from app.extensions import db

app = create_app()

@app.route('/', methods=['GET', 'POST'])
def migrate():
    """Create missing tables"""
    try:
        with app.app_context():
            # Import all models to ensure they're registered
            from app.models.meal_comment import MealComment
            from app.models.patient_invitation import PatientInvitation

            # Create all tables (will skip existing ones)
            db.create_all()

        return jsonify({"message": "Tables created successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e), "type": type(e).__name__}), 500
