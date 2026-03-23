import os
import logging

import resend
from itsdangerous import URLSafeTimedSerializer

logger = logging.getLogger(__name__)

resend.api_key = os.getenv("RESEND_API_KEY", "")

_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "onboarding@resend.dev")
_FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
_SECRET_KEY = os.getenv("SECRET_KEY", "dev-app-secret-key")

_serializer = URLSafeTimedSerializer(_SECRET_KEY)


def generate_verification_token(email: str) -> str:
    return _serializer.dumps(email, salt="email-verify")


def verify_token(token: str, max_age: int = 86400) -> str | None:
    """Decode a verification token. Returns email or None if invalid/expired."""
    try:
        return _serializer.loads(token, salt="email-verify", max_age=max_age)
    except Exception:
        return None


_API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:5000/api/v1")


def send_verification_email(email: str, first_name: str, token: str):
    verify_url = f"{_API_URL}/auth/verify-email?token={token}"

    html = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 480px; margin: 0 auto; padding: 32px;">
        <div style="text-align: center; margin-bottom: 24px;">
            <h1 style="color: #1b87f5; font-size: 28px; margin: 0;">Wellvio</h1>
        </div>
        <h2 style="color: #1a1a2e; font-size: 20px;">¡Hola {first_name}!</h2>
        <p style="color: #4a4a68; font-size: 15px; line-height: 1.6;">
            Gracias por registrarte en Wellvio. Para activar tu cuenta, hacé clic en el siguiente botón:
        </p>
        <div style="text-align: center; margin: 32px 0;">
            <a href="{verify_url}"
               style="background-color: #1b87f5; color: white; padding: 14px 32px;
                      border-radius: 8px; text-decoration: none; font-weight: 600;
                      font-size: 15px; display: inline-block;">
                Verificar mi email
            </a>
        </div>
        <p style="color: #8a8aa3; font-size: 13px; line-height: 1.5;">
            Si no creaste una cuenta en Wellvio, podés ignorar este email.
            El enlace expira en 24 horas.
        </p>
        <hr style="border: none; border-top: 1px solid #e8e8f0; margin: 24px 0;" />
        <p style="color: #8a8aa3; font-size: 12px; text-align: center;">
            &copy; Wellvio — Seguí tu progreso físico
        </p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": f"Wellvio <{_FROM_EMAIL}>",
            "to": [email],
            "subject": "Verificá tu email — Wellvio",
            "html": html,
        })
        logger.info(f"Verification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {e}")
        raise
