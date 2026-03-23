import os
import logging

import requests as http_requests
from flask import Blueprint, jsonify, request, redirect
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, current_user,
)
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.extensions import db
from app.models.user import User, Profile, ProfessionalPatient
from app.models.weigh_in import WeighIn
from app.services.storage import get_storage
from app.services.email import generate_verification_token, verify_token, send_verification_email
from app.utils.errors import validation_error, api_error
from app.utils.validators import validate_email, validate_password

logger = logging.getLogger(__name__)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _weight_stats(user_id):
    """Return initial (oldest) and current (newest) weigh-in for a user."""
    oldest = (
        WeighIn.query
        .filter_by(patient_id=user_id)
        .order_by(WeighIn.recorded_at.asc())
        .first()
    )
    newest = (
        WeighIn.query
        .filter_by(patient_id=user_id)
        .order_by(WeighIn.recorded_at.desc())
        .first()
    )
    return {
        "initial_weight_kg": float(oldest.weight_kg) if oldest else None,
        "initial_weight_date": oldest.recorded_at.isoformat() if oldest else None,
        "current_weight_kg": float(newest.weight_kg) if newest else None,
        "current_weight_date": newest.recorded_at.isoformat() if newest else None,
    }

def _my_professional(user_id):
    """Return the assigned professional's public info for a patient."""
    assignment = (
        ProfessionalPatient.query
        .filter_by(patient_id=user_id, is_active=True)
        .first()
    )
    if not assignment:
        return None
    prof = db.session.get(User, assignment.professional_id)
    if not prof:
        return None
    prof_profile = prof.profile
    return {
        "first_name": prof.first_name,
        "last_name": prof.last_name,
        "email": prof.email,
        "phone": prof_profile.phone if prof_profile else None,
        "bio": prof_profile.bio if prof_profile else None,
    }


def _build_user_response(user):
    """Build standard user data dict with weight stats and professional info."""
    user_data = user.to_dict(include_profile=True)
    user_data["weight_stats"] = _weight_stats(user.id)
    if user.role == "patient":
        user_data["my_professional"] = _my_professional(user.id)
    return user_data


bp = Blueprint("auth", __name__)


@bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    gender = (data.get("gender") or "").strip() or None

    if not email or not validate_email(email):
        return validation_error("Valid email is required", "email")
    if not first_name or not last_name:
        return validation_error("First name and last name are required")

    pw_err = validate_password(password)
    if pw_err:
        return validation_error(pw_err, "password")

    existing = User.query.filter_by(email=email).first()
    if existing:
        if existing.oauth_provider and not existing.password_hash:
            # Google-only user registering with password — link account
            existing.set_password(password)
            existing.first_name = first_name
            existing.last_name = last_name
            if gender:
                existing.gender = gender
            db.session.commit()
            return jsonify(message="verification_email_sent"), 201
        return api_error("Email already registered", 409)

    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        gender=gender,
        role="patient",
        email_verified=False,
    )
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    profile = Profile(user_id=user.id)
    db.session.add(profile)
    db.session.commit()

    # Send verification email
    try:
        token = generate_verification_token(email)
        send_verification_email(email, first_name, token)
    except Exception:
        logger.warning(f"Could not send verification email to {email}")

    return jsonify(message="verification_email_sent"), 201


@bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return validation_error("Email and password are required")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return api_error("Invalid email or password", 401)

    if not user.is_active:
        return api_error("Account is deactivated", 403)

    if not user.email_verified:
        return jsonify(error="email_not_verified", message="Please verify your email before logging in"), 403

    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    return jsonify(
        user=_build_user_response(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@bp.route("/verify-email", methods=["GET"])
def verify_email():
    token = request.args.get("token", "")
    if not token:
        return redirect(f"{FRONTEND_URL}/verify-email?status=error")

    email = verify_token(token)
    if not email:
        return redirect(f"{FRONTEND_URL}/verify-email?status=expired")

    user = User.query.filter_by(email=email).first()
    if not user:
        return redirect(f"{FRONTEND_URL}/verify-email?status=error")

    if user.email_verified:
        return redirect(f"{FRONTEND_URL}/verify-email?status=already_verified")

    user.email_verified = True
    db.session.commit()

    return redirect(f"{FRONTEND_URL}/verify-email?status=success")


@bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()

    if not email:
        return validation_error("Email is required", "email")

    user = User.query.filter_by(email=email).first()
    if not user:
        # Don't reveal if user exists
        return jsonify(message="verification_email_sent"), 200

    if user.email_verified:
        return jsonify(message="already_verified"), 200

    try:
        token = generate_verification_token(email)
        send_verification_email(email, user.first_name, token)
    except Exception:
        return api_error("Failed to send verification email", 500)

    return jsonify(message="verification_email_sent"), 200


def _exchange_google_code(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for user info via Google's token + userinfo endpoints."""
    # Exchange code for tokens
    token_resp = http_requests.post("https://oauth2.googleapis.com/token", data={
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    })
    if token_resp.status_code != 200:
        logger.error(f"Google token exchange failed: {token_resp.text}")
        return {}
    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    if not access_token:
        return {}

    # Get user info
    userinfo_resp = http_requests.get(
        "https://www.googleapis.com/oauth2/v2/userinfo",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    if userinfo_resp.status_code != 200:
        return {}
    return userinfo_resp.json()


@bp.route("/google", methods=["POST"])
def google_auth():
    data = request.get_json(silent=True) or {}
    credential = data.get("credential", "")
    code = data.get("code", "")
    redirect_uri = data.get("redirect_uri", "")

    if not credential and not code:
        return validation_error("Google credential or code is required")

    if not GOOGLE_CLIENT_ID:
        return api_error("Google auth is not configured", 500)

    if code:
        # OAuth 2.0 authorization code flow
        userinfo = _exchange_google_code(code, redirect_uri)
        if not userinfo:
            return api_error("Failed to exchange Google auth code", 401)
        google_id = userinfo.get("id", "")
        email = userinfo.get("email", "").lower()
        first_name = userinfo.get("given_name", "")
        last_name = userinfo.get("family_name", "")
        email_verified = userinfo.get("verified_email", False)
    else:
        # ID token flow (One Tap / hidden button)
        try:
            idinfo = google_id_token.verify_oauth2_token(
                credential, google_requests.Request(), GOOGLE_CLIENT_ID
            )
        except ValueError:
            return api_error("Invalid Google token", 401)
        google_id = idinfo["sub"]
        email = idinfo.get("email", "").lower()
        first_name = idinfo.get("given_name", "")
        last_name = idinfo.get("family_name", "")
        email_verified = idinfo.get("email_verified", False)

    if not email or not email_verified:
        return api_error("Google account email not verified", 400)

    # Check if user exists by OAuth ID or email
    user = User.query.filter_by(oauth_provider="google", oauth_id=google_id).first()

    if not user:
        user = User.query.filter_by(email=email).first()
        if user:
            # Link existing account with Google
            user.oauth_provider = "google"
            user.oauth_id = google_id
            user.email_verified = True
        else:
            # Create new user
            user = User(
                email=email,
                first_name=first_name or "User",
                last_name=last_name or "",
                role="patient",
                email_verified=True,
                oauth_provider="google",
                oauth_id=google_id,
            )
            db.session.add(user)
            db.session.flush()
            profile = Profile(user_id=user.id)
            db.session.add(profile)

    if not user.is_active:
        return api_error("Account is deactivated", 403)

    # Ensure verified
    user.email_verified = True
    db.session.commit()

    access_token = create_access_token(identity=user)
    refresh_token = create_refresh_token(identity=user)

    return jsonify(
        user=_build_user_response(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    access_token = create_access_token(identity=get_jwt_identity())
    return jsonify(access_token=access_token)


@bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    return jsonify(user=_build_user_response(current_user))


@bp.route("/me", methods=["PATCH"])
@jwt_required()
def update_me():
    data = request.get_json(silent=True) or {}
    user = current_user

    if "first_name" in data:
        fname = (data["first_name"] or "").strip()
        if not fname:
            return validation_error("First name cannot be empty", "first_name")
        user.first_name = fname
    if "last_name" in data:
        lname = (data["last_name"] or "").strip()
        if not lname:
            return validation_error("Last name cannot be empty", "last_name")
        user.last_name = lname
    if "gender" in data:
        user.gender = (data["gender"] or "").strip() or None

    profile = user.profile
    if not profile:
        profile = Profile(user_id=user.id)
        db.session.add(profile)

    for field in ("bio", "phone", "date_of_birth", "height_cm"):
        if field in data:
            setattr(profile, field, data[field])

    db.session.commit()
    return jsonify(user=_build_user_response(user))


@bp.route("/me/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    file = request.files.get("photo")
    if not file:
        return validation_error("Photo file is required", "photo")

    storage = get_storage()
    profile = current_user.profile
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.session.add(profile)

    # Delete old avatar if exists
    if profile.avatar_storage_key:
        try:
            storage.delete(profile.avatar_storage_key)
        except Exception:
            pass

    result = storage.upload(file, folder="avatars")
    profile.avatar_storage_key = result["storage_key"]
    db.session.commit()

    return jsonify(user=_build_user_response(current_user))
