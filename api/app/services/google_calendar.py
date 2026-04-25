"""Google Calendar integration service.

Handles per-user OAuth tokens (with auto-refresh) and direct REST calls
against the Google Calendar API to create/update/delete events tied to
Wellvio appointments.

We hit the REST API with `requests` rather than pulling in the full
google-api-python-client; only a handful of endpoints are needed.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import requests

from app.extensions import db
from app.models.google_calendar_token import GoogleCalendarToken

logger = logging.getLogger(__name__)

SCOPE = "https://www.googleapis.com/auth/calendar.events"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
REVOKE_URL = "https://oauth2.googleapis.com/revoke"
USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"

# Refresh access tokens this many seconds before they actually expire,
# to avoid races with calendar API calls firing right at the edge.
EXPIRY_LEEWAY_SECONDS = 60


def _client_id() -> str:
    return os.environ.get("GOOGLE_CLIENT_ID", "")


def _client_secret() -> str:
    return os.environ.get("GOOGLE_CLIENT_SECRET", "")


def _redirect_uri() -> str:
    return os.environ.get(
        "GOOGLE_OAUTH_REDIRECT_URI",
        "http://localhost:5000/api/v1/auth/google/calendar/callback",
    )


def is_configured() -> bool:
    return bool(_client_id() and _client_secret())


# --- OAuth flow helpers ---

def build_auth_url(state: str) -> str:
    params = {
        "client_id": _client_id(),
        "redirect_uri": _redirect_uri(),
        "response_type": "code",
        "scope": f"{SCOPE} openid email",
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str) -> dict:
    """Exchange an authorization code for tokens. Raises on error."""
    res = requests.post(
        TOKEN_URL,
        data={
            "code": code,
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "redirect_uri": _redirect_uri(),
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    res.raise_for_status()
    return res.json()


def fetch_userinfo(access_token: str) -> dict:
    res = requests.get(
        USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    res.raise_for_status()
    return res.json()


def store_tokens(user_id, token_response: dict, google_email: Optional[str] = None) -> GoogleCalendarToken:
    """Persist a fresh token bundle for a user. Replaces any existing record."""
    expires_in = int(token_response.get("expires_in", 3600))
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

    record = GoogleCalendarToken.query.filter_by(user_id=user_id).first()
    if record is None:
        record = GoogleCalendarToken(user_id=user_id)
        db.session.add(record)

    record.access_token = token_response["access_token"]
    # Google only returns refresh_token on the first consent (or when prompt=consent).
    # If we asked for prompt=consent we should always get one back.
    if token_response.get("refresh_token"):
        record.refresh_token = token_response["refresh_token"]
    record.expires_at = expires_at
    record.scope = token_response.get("scope", SCOPE)
    if google_email:
        record.google_email = google_email
    db.session.commit()
    return record


def get_connection(user_id) -> Optional[GoogleCalendarToken]:
    return GoogleCalendarToken.query.filter_by(user_id=user_id).first()


def disconnect(user_id) -> bool:
    record = get_connection(user_id)
    if record is None:
        return False
    # Best-effort revoke at Google's side; ignore failures.
    try:
        requests.post(REVOKE_URL, params={"token": record.refresh_token}, timeout=5)
    except Exception:
        logger.warning("Failed to revoke Google token for user %s", user_id, exc_info=True)
    db.session.delete(record)
    db.session.commit()
    return True


# --- Token refresh ---

def _refresh_if_needed(record: GoogleCalendarToken) -> str:
    """Return a valid access token, refreshing if necessary. Raises on failure."""
    now = datetime.now(timezone.utc)
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at - timedelta(seconds=EXPIRY_LEEWAY_SECONDS) > now:
        return record.access_token

    res = requests.post(
        TOKEN_URL,
        data={
            "client_id": _client_id(),
            "client_secret": _client_secret(),
            "refresh_token": record.refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    res.raise_for_status()
    payload = res.json()
    record.access_token = payload["access_token"]
    expires_in = int(payload.get("expires_in", 3600))
    record.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    if payload.get("refresh_token"):
        record.refresh_token = payload["refresh_token"]
    db.session.commit()
    return record.access_token


# --- Calendar API ---

def _appointment_to_event(appointment) -> dict:
    """Build the Google Calendar event payload from a Wellvio appointment."""
    start = appointment.scheduled_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(minutes=int(appointment.duration_minutes or 30))

    summary = f"Wellvio: {appointment.title}"
    description_parts = []
    if appointment.notes:
        description_parts.append(appointment.notes)
    description_parts.append(
        "Turno gestionado desde Wellvio. No edites este evento manualmente — los cambios deben hacerse en Wellvio."
    )

    return {
        "summary": summary,
        "description": "\n\n".join(description_parts),
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        "source": {"title": "Wellvio", "url": os.environ.get("FRONTEND_URL", "")},
        # Set a stable extendedProperty so we can recognise our own events later.
        "extendedProperties": {
            "private": {
                "wellvio_appointment_id": str(appointment.id),
            }
        },
    }


def create_event(appointment) -> Optional[str]:
    """Push a new event to the professional's calendar. Returns the event id or None."""
    record = get_connection(appointment.professional_id)
    if record is None:
        return None
    try:
        access_token = _refresh_if_needed(record)
        res = requests.post(
            f"{CALENDAR_API_BASE}/calendars/{record.calendar_id}/events",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=_appointment_to_event(appointment),
            timeout=10,
        )
        res.raise_for_status()
        return res.json().get("id")
    except Exception:
        logger.warning(
            "Google Calendar create_event failed for appointment %s",
            appointment.id,
            exc_info=True,
        )
        return None


def update_event(appointment) -> bool:
    """Patch an existing event after the appointment changes. Returns True on success."""
    if not appointment.google_event_id:
        return False
    record = get_connection(appointment.professional_id)
    if record is None:
        return False
    try:
        access_token = _refresh_if_needed(record)
        res = requests.patch(
            f"{CALENDAR_API_BASE}/calendars/{record.calendar_id}/events/{appointment.google_event_id}",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json=_appointment_to_event(appointment),
            timeout=10,
        )
        res.raise_for_status()
        return True
    except Exception:
        logger.warning(
            "Google Calendar update_event failed for appointment %s",
            appointment.id,
            exc_info=True,
        )
        return False


def delete_event(appointment) -> bool:
    """Delete the synced event. Returns True if Google accepted the delete (or it was already gone)."""
    if not appointment.google_event_id:
        return False
    record = get_connection(appointment.professional_id)
    if record is None:
        return False
    try:
        access_token = _refresh_if_needed(record)
        res = requests.delete(
            f"{CALENDAR_API_BASE}/calendars/{record.calendar_id}/events/{appointment.google_event_id}",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        # 410 Gone = already deleted, treat as success.
        if res.status_code in (200, 204, 404, 410):
            return True
        res.raise_for_status()
        return True
    except Exception:
        logger.warning(
            "Google Calendar delete_event failed for appointment %s",
            appointment.id,
            exc_info=True,
        )
        return False
