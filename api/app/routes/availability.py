from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.availability import ProfessionalAvailability, AvailabilityOverride
from app.models.appointment import Appointment
from app.models.notification import Notification, NotificationRecipient
from app.models.user import User
from app.services.rbac import is_assigned_professional
from app.services import google_calendar as gcal
from app.utils.errors import validation_error, api_error
from app.utils.validators import parse_date

bp = Blueprint("availability", __name__)

# Wall-clock times in the availability schedule are interpreted as local time
# in this zone — the app is AR-only today.
LOCAL_TZ = ZoneInfo("America/Argentina/Buenos_Aires")


def _local_dt(target_date, time_str):
    h, m = map(int, time_str.split(":"))
    return datetime(target_date.year, target_date.month, target_date.day, h, m, tzinfo=LOCAL_TZ)


# --- Helpers ---

def _compute_slots(professional_id, target_date):
    """Compute available time slots for a professional on a given date."""
    now_utc = datetime.now(timezone.utc)
    today_local = now_utc.astimezone(LOCAL_TZ).date()

    if target_date < today_local:
        return [], None, 30

    # Get weekly rules for this day of week (supports multiple intervals)
    rules = ProfessionalAvailability.query.filter_by(
        professional_id=professional_id,
        day_of_week=target_date.weekday(),
        is_active=True,
    ).all()

    # Use first rule for settings (slot_duration, booking_window)
    rule = rules[0] if rules else None

    # Check booking window
    if rule:
        max_date = today_local + timedelta(days=rule.booking_window_days)
        if target_date > max_date:
            return [], rule, rule.slot_duration_minutes

    # Check overrides for this date
    overrides = AvailabilityOverride.query.filter_by(
        professional_id=professional_id,
        override_date=target_date,
    ).all()

    block_overrides = [o for o in overrides if o.override_type == "block"]
    extra_overrides = [o for o in overrides if o.override_type == "extra"]

    # Collect time windows. Each window carries (start, end, is_online_only).
    windows = []

    # Full-day block check
    full_day_blocked = any(o.start_time is None for o in block_overrides)
    if full_day_blocked:
        # Only extra windows apply
        pass
    elif rules:
        for r in rules:
            windows.append((r.start_time, r.end_time, bool(r.is_online_only)))

    # Add extra override windows (overrides do not currently support online-only)
    for o in extra_overrides:
        if o.start_time and o.end_time:
            windows.append((o.start_time, o.end_time, False))

    if not windows:
        return [], rule, rule.slot_duration_minutes if rule else 30

    # Determine slot duration from rule or first available rule for this professional
    if rule:
        slot_duration = rule.slot_duration_minutes
    else:
        any_rule = ProfessionalAvailability.query.filter_by(
            professional_id=professional_id, is_active=True
        ).first()
        slot_duration = any_rule.slot_duration_minutes if any_rule else 30

    # Generate slots from windows. Each slot is (datetime, is_online_only).
    duration = timedelta(minutes=slot_duration)
    all_slots: list[tuple[datetime, bool]] = []

    for win_start_str, win_end_str, win_online_only in windows:
        slot_start = _local_dt(target_date, win_start_str)
        window_end = _local_dt(target_date, win_end_str)

        while slot_start + duration <= window_end:
            # Skip past slots
            if slot_start > now_utc:
                all_slots.append((slot_start, win_online_only))
            slot_start += duration

    # Remove partial-day blocked ranges
    for o in block_overrides:
        if o.start_time and o.end_time:
            block_start = _local_dt(target_date, o.start_time)
            block_end = _local_dt(target_date, o.end_time)
            all_slots = [(s, oo) for (s, oo) in all_slots if not (s >= block_start and s < block_end)]

    # Remove slots that overlap with existing appointments. Anchor the day
    # in local time so the UTC range matches what the user considers "today".
    day_start = datetime(
        target_date.year, target_date.month, target_date.day, tzinfo=LOCAL_TZ
    )
    day_end = day_start + timedelta(days=1)

    booked = Appointment.query.filter(
        Appointment.professional_id == professional_id,
        Appointment.status == "scheduled",
        Appointment.scheduled_at >= day_start,
        Appointment.scheduled_at < day_end,
    ).all()

    for appt in booked:
        appt_start = appt.scheduled_at.replace(tzinfo=timezone.utc) if appt.scheduled_at.tzinfo is None else appt.scheduled_at
        appt_end = appt_start + timedelta(minutes=appt.duration_minutes)
        all_slots = [
            (s, oo) for (s, oo) in all_slots
            if not (s < appt_end and s + duration > appt_start)
        ]

    all_slots.sort(key=lambda t: t[0])
    return all_slots, rule, slot_duration


# --- Public: View Professional Info & Slots (no auth) ---

@bp.route("/<uuid:professional_id>/public", methods=["GET"])
def get_public_profile(professional_id):
    """Get a professional's public info for the booking page. No auth required."""
    user = db.session.get(User, professional_id)
    if not user or user.role not in ("professional", "devadmin"):
        return api_error("Professional not found", 404)

    profile = user.profile
    return jsonify(
        id=str(user.id),
        first_name=user.first_name,
        last_name=user.last_name,
        bio=profile.bio if profile else None,
        avatar_url=profile.to_dict().get("avatar_url") if profile else None,
    )


@bp.route("/<uuid:professional_id>/public/slots", methods=["GET"])
def get_public_slots(professional_id):
    """Get available time slots for a specific date. No auth required."""
    user = db.session.get(User, professional_id)
    if not user or user.role not in ("professional", "devadmin"):
        return api_error("Professional not found", 404)

    date_str = request.args.get("date")
    target_date = parse_date(date_str)
    if not target_date:
        return validation_error("Valid date parameter is required (YYYY-MM-DD)")

    slots, rule, slot_duration = _compute_slots(professional_id, target_date)

    return jsonify(
        date=target_date.isoformat(),
        slots=[
            {"time": s.strftime("%H:%M"), "is_online_only": oo}
            for (s, oo) in slots
        ],
        slot_duration_minutes=slot_duration,
    )


@bp.route("/<uuid:professional_id>/public/book", methods=["POST"])
def public_book_appointment(professional_id):
    """Public booking — anyone can book by providing name, email, and optional phone."""
    user = db.session.get(User, professional_id)
    if not user or user.role not in ("professional", "devadmin"):
        return api_error("Professional not found", 404)

    data = request.get_json(silent=True) or {}
    guest_name = (data.get("name") or "").strip()
    guest_email = (data.get("email") or "").strip()
    guest_phone = (data.get("phone") or "").strip() or None
    date_str = data.get("date")
    slot_time = data.get("slot_time")
    notes = (data.get("notes") or "").strip() or None

    if not guest_name:
        return validation_error("Name is required")
    if not guest_email:
        return validation_error("Email is required")
    if not date_str or not slot_time:
        return validation_error("date and slot_time are required")

    target_date = parse_date(date_str)
    if not target_date:
        return validation_error("Invalid date format")

    available_slots, rule, slot_duration = _compute_slots(professional_id, target_date)

    try:
        scheduled_at = _local_dt(target_date, slot_time)
    except (ValueError, TypeError):
        return validation_error("Invalid slot_time format (HH:MM)")

    if not any(s == scheduled_at for (s, _oo) in available_slots):
        return api_error("This time slot is not available", 409)

    # Build title from guest info
    title = guest_name
    appt_notes = f"Email: {guest_email}"
    if guest_phone:
        appt_notes += f" | Phone: {guest_phone}"
    if notes:
        appt_notes += f"\n{notes}"

    appointment = Appointment(
        patient_id=None,
        professional_id=professional_id,
        scheduled_at=scheduled_at,
        duration_minutes=slot_duration,
        title=title,
        notes=appt_notes,
        booking_source="public_link",
    )
    db.session.add(appointment)

    # Notify professional
    pro_notif = Notification(
        author_id=professional_id,
        title="appointment_booked_public",
        body=f"{title} - {scheduled_at.strftime('%Y-%m-%d %H:%M')}",
    )
    db.session.add(pro_notif)
    db.session.flush()
    db.session.add(NotificationRecipient(
        notification_id=pro_notif.id,
        patient_id=professional_id,
    ))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return api_error("This slot was just taken. Please select another.", 409)

    event_id = gcal.create_event(appointment)
    if event_id:
        appointment.google_event_id = event_id
        db.session.commit()

    return jsonify(data=appointment.to_dict()), 201


# --- Professional: Manage Schedule ---

@bp.route("/<uuid:professional_id>", methods=["GET"])
@jwt_required()
def get_availability(professional_id):
    """Get a professional's full availability schedule and overrides."""
    schedule = ProfessionalAvailability.query.filter_by(
        professional_id=professional_id
    ).order_by(ProfessionalAvailability.day_of_week).all()

    overrides = AvailabilityOverride.query.filter_by(
        professional_id=professional_id
    ).filter(
        AvailabilityOverride.override_date >= date.today()
    ).order_by(AvailabilityOverride.override_date).all()

    return jsonify(
        schedule=[s.to_dict() for s in schedule],
        overrides=[o.to_dict() for o in overrides],
    )


@bp.route("/<uuid:professional_id>/schedule", methods=["PUT"])
@jwt_required()
def update_schedule(professional_id):
    """Replace the professional's weekly schedule. Atomic delete-and-reinsert."""
    if current_user.role not in ("professional", "devadmin"):
        return api_error("Only professionals can manage availability", 403)
    if current_user.role == "professional" and str(current_user.id) != str(professional_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    rules = data.get("rules", [])
    slot_duration = data.get("slot_duration_minutes", 30)
    booking_window = data.get("booking_window_days", 30)

    if not isinstance(rules, list):
        return validation_error("rules must be an array")

    # Validate rules
    for rule in rules:
        dow = rule.get("day_of_week")
        if dow is None or not (0 <= dow <= 6):
            return validation_error("day_of_week must be 0-6")

        start = rule.get("start_time", "")
        end = rule.get("end_time", "")
        if not start or not end:
            return validation_error("start_time and end_time are required")
        if start >= end:
            return validation_error(f"start_time must be before end_time for day {dow}")

    # Delete existing rules
    ProfessionalAvailability.query.filter_by(
        professional_id=professional_id
    ).delete()

    # Insert new rules
    for rule in rules:
        avail = ProfessionalAvailability(
            professional_id=professional_id,
            day_of_week=rule["day_of_week"],
            start_time=rule["start_time"],
            end_time=rule["end_time"],
            slot_duration_minutes=slot_duration,
            booking_window_days=booking_window,
            is_active=True,
            is_online_only=bool(rule.get("is_online_only", False)),
        )
        db.session.add(avail)

    db.session.commit()

    schedule = ProfessionalAvailability.query.filter_by(
        professional_id=professional_id
    ).order_by(ProfessionalAvailability.day_of_week).all()

    return jsonify(schedule=[s.to_dict() for s in schedule])


@bp.route("/<uuid:professional_id>/overrides", methods=["POST"])
@jwt_required()
def create_override(professional_id):
    """Add a date-level override (block or extra hours)."""
    if current_user.role not in ("professional", "devadmin"):
        return api_error("Only professionals can manage availability", 403)
    if current_user.role == "professional" and str(current_user.id) != str(professional_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    override_date = parse_date(data.get("override_date"))
    override_type = data.get("override_type")

    if not override_date:
        return validation_error("Valid override_date is required (YYYY-MM-DD)")
    if override_type not in ("block", "extra"):
        return validation_error("override_type must be 'block' or 'extra'")
    if override_date < date.today():
        return validation_error("Cannot create overrides for past dates")

    start_time = data.get("start_time")
    end_time = data.get("end_time")

    if override_type == "extra":
        if not start_time or not end_time:
            return validation_error("start_time and end_time are required for extra overrides")
        if start_time >= end_time:
            return validation_error("start_time must be before end_time")

    override = AvailabilityOverride(
        professional_id=professional_id,
        override_date=override_date,
        override_type=override_type,
        start_time=start_time,
        end_time=end_time,
    )
    db.session.add(override)
    db.session.commit()

    return jsonify(data=override.to_dict()), 201


@bp.route("/<uuid:professional_id>/overrides/<uuid:override_id>", methods=["DELETE"])
@jwt_required()
def delete_override(professional_id, override_id):
    """Remove a date-level override."""
    if current_user.role not in ("professional", "devadmin"):
        return api_error("Only professionals can manage availability", 403)
    if current_user.role == "professional" and str(current_user.id) != str(professional_id):
        return api_error("Forbidden", 403)

    override = db.session.get(AvailabilityOverride, override_id)
    if not override or str(override.professional_id) != str(professional_id):
        return api_error("Override not found", 404)

    db.session.delete(override)
    db.session.commit()
    return jsonify(message="Override deleted")


# --- Patient: View Slots & Book ---

@bp.route("/<uuid:professional_id>/slots", methods=["GET"])
@jwt_required()
def get_slots(professional_id):
    """Get available time slots for a specific date."""
    date_str = request.args.get("date")
    target_date = parse_date(date_str)

    if not target_date:
        return validation_error("Valid date parameter is required (YYYY-MM-DD)")

    slots, rule, slot_duration = _compute_slots(professional_id, target_date)

    return jsonify(
        date=target_date.isoformat(),
        slots=[
            {"time": s.strftime("%H:%M"), "is_online_only": oo}
            for (s, oo) in slots
        ],
        slot_duration_minutes=slot_duration,
    )


@bp.route("/<uuid:professional_id>/book", methods=["POST"])
@jwt_required()
def book_appointment(professional_id):
    """Patient self-books an appointment from available slots."""
    if current_user.role != "patient":
        return api_error("Only patients can use self-booking", 403)

    # Check assignment
    if not is_assigned_professional(professional_id, current_user.id):
        return api_error("You are not assigned to this professional", 403)

    data = request.get_json(silent=True) or {}
    date_str = data.get("date")
    slot_time = data.get("slot_time")
    notes = (data.get("notes") or "").strip() or None

    if not date_str or not slot_time:
        return validation_error("date and slot_time are required")

    target_date = parse_date(date_str)
    if not target_date:
        return validation_error("Invalid date format")

    # Re-compute slots to verify availability (server-side double-check)
    available_slots, rule, slot_duration = _compute_slots(professional_id, target_date)

    # Parse requested time
    try:
        scheduled_at = _local_dt(target_date, slot_time)
    except (ValueError, TypeError):
        return validation_error("Invalid slot_time format (HH:MM)")

    # Verify this slot is actually available
    if not any(s == scheduled_at for (s, _oo) in available_slots):
        return api_error("This time slot is not available", 409)

    # Create appointment
    title = f"{current_user.first_name} {current_user.last_name}"
    appointment = Appointment(
        patient_id=current_user.id,
        professional_id=professional_id,
        scheduled_at=scheduled_at,
        duration_minutes=slot_duration,
        title=title,
        notes=notes,
        booking_source="patient_self",
    )
    db.session.add(appointment)

    # Notify patient
    patient_notif = Notification(
        author_id=current_user.id,
        title="appointment_booked",
        body=f"{title} - {scheduled_at.strftime('%Y-%m-%d %H:%M')}",
    )
    db.session.add(patient_notif)
    db.session.flush()
    db.session.add(NotificationRecipient(
        notification_id=patient_notif.id,
        patient_id=current_user.id,
    ))

    # Notify professional
    pro_notif = Notification(
        author_id=current_user.id,
        title="appointment_booked_pro",
        body=f"{title} - {scheduled_at.strftime('%Y-%m-%d %H:%M')}",
    )
    db.session.add(pro_notif)
    db.session.flush()
    db.session.add(NotificationRecipient(
        notification_id=pro_notif.id,
        patient_id=professional_id,  # patient_id column is generic user FK
    ))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return api_error("This slot was just taken. Please select another.", 409)

    event_id = gcal.create_event(appointment)
    if event_id:
        appointment.google_event_id = event_id
        db.session.commit()

    return jsonify(data=appointment.to_dict()), 201
