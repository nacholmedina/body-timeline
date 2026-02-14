"""Vercel serverless entry point for the Flask API."""
from app import create_app

app = create_app()
