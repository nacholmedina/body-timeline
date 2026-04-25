"""Google Calendar connection endpoints.

A user-initiated OAuth code-flow that issues a refresh token so the
backend can push appointment events into the professional's primary
calendar even when they're not actively using Wellvio.
"""
import os
import secrets

from flask import Blueprint, jsonify, redirect, request
from flask_jwt_extended import create_access_token, decode_token, current_user, jwt_required
from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.services import google_calendar
from app.utils.errors import api_error, validation_error

bp = Blueprint("google_calendar", __name__)


STATE_MAX_AGE = 600  # seconds


def _state_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=os.environ.get("SECRET_KEY", "dev"),
        salt="google-calendar-oauth",
    )


def _frontend_url(path: str) -> str:
    base = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    return f"{base}{path}"


@bp.route("/connect", methods=["GET"])
@jwt_required()
def connect():
    """Return the URL the frontend should redirect the user to for consent."""
    if not google_calendar.is_configured():
        return api_error("Google Calendar is not configured on this server", 503)

    state = _state_serializer().dumps({
        "user_id": str(current_user.id),
        "nonce": secrets.token_urlsafe(16),
    })
    auth_url = google_calendar.build_auth_url(state)
    return jsonify(authorization_url=auth_url)


@bp.route("/callback", methods=["GET"])
def callback():
    """Google redirects here after the user grants (or denies) consent."""
    error = request.args.get("error")
    if error:
        return redirect(_frontend_url(f"/app/professional/calendar?google_calendar=denied"))

    code = request.args.get("code")
    state = request.args.get("state")
    if not code or not state:
        return redirect(_frontend_url("/app/professional/calendar?google_calendar=invalid"))

    try:
        payload = _state_serializer().loads(state, max_age=STATE_MAX_AGE)
    except BadSignature:
        return redirect(_frontend_url("/app/professional/calendar?google_calendar=invalid"))

    user_id = payload.get("user_id")
    if not user_id:
        return redirect(_frontend_url("/app/professional/calendar?google_calendar=invalid"))

    try:
        token_payload = google_calendar.exchange_code(code)
    except Exception:
        return redirect(_frontend_url("/app/professional/calendar?google_calendar=exchange_failed"))

    google_email = None
    try:
        info = google_calendar.fetch_userinfo(token_payload["access_token"])
        google_email = info.get("email")
    except Exception:
        pass  # not critical

    google_calendar.store_tokens(user_id, token_payload, google_email=google_email)
    return redirect(_frontend_url("/app/professional/calendar?google_calendar=connected"))


@bp.route("/status", methods=["GET"])
@jwt_required()
def status():
    record = google_calendar.get_connection(current_user.id)
    if record is None:
        return jsonify(connected=False, configured=google_calendar.is_configured())
    return jsonify(
        connected=True,
        configured=True,
        google_email=record.google_email,
        calendar_id=record.calendar_id,
        connected_at=record.created_at.isoformat(),
    )


@bp.route("/disconnect", methods=["POST"])
@jwt_required()
def disconnect():
    google_calendar.disconnect(current_user.id)
    return jsonify(connected=False)
