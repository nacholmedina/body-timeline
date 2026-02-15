"""
One-time migration endpoint - DELETE AFTER USE
"""
from flask import Flask, jsonify
from flask_migrate import upgrade as flask_migrate_upgrade
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app

app = create_app()

@app.route('/', methods=['GET', 'POST'])
def migrate():
    """Run database migrations"""
    try:
        with app.app_context():
            flask_migrate_upgrade()
        return jsonify({"message": "Migrations applied successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
