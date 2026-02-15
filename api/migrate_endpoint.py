"""
One-time migration endpoint - DELETE AFTER USE
"""
from flask import jsonify
from flask_migrate import upgrade
from app import create_app

app = create_app()

def handler(request):
    """Vercel serverless function to run migrations"""
    try:
        with app.app_context():
            upgrade()
        return jsonify({"message": "Migrations applied successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
