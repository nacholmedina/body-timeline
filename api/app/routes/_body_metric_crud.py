"""Reusable CRUD blueprint factory for body-metric log tables.

All five metric tables (body fat, muscle mass, waist, hips, neck) share
the same shape (id, patient_id, value, recorded_at, notes) and the same
RBAC rules as `weigh_ins`, so the routes are generated once instead of
duplicated across five files.
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.services.body_metrics import MetricSpec, clean_notes, validate_value_in_range
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.utils.errors import api_error, validation_error
from app.utils.validators import get_pagination_params, parse_datetime


def make_body_metric_blueprint(name: str, model, spec: MetricSpec) -> Blueprint:
    bp = Blueprint(name, __name__)

    @bp.route("", methods=["GET"])
    @jwt_required()
    def list_entries():
        patient_ids = get_accessible_patient_ids(current_user)
        query = model.query

        if patient_ids is not None:
            query = query.filter(model.patient_id.in_(patient_ids))

        pid = request.args.get("patient_id")
        if pid:
            if not can_access_patient_data(current_user, pid):
                return api_error("Forbidden", 403)
            query = query.filter_by(patient_id=pid)

        date_from = parse_datetime(request.args.get("from"))
        date_to = parse_datetime(request.args.get("to"))
        if date_from:
            query = query.filter(model.recorded_at >= date_from)
        if date_to:
            query = query.filter(model.recorded_at <= date_to)

        query = query.order_by(model.recorded_at.desc())
        page, limit, offset = get_pagination_params(request.args)
        total = query.count()
        items = query.offset(offset).limit(limit).all()

        return jsonify(
            data=[i.to_dict() for i in items], page=page, limit=limit, total=total
        )

    @bp.route("", methods=["POST"])
    @jwt_required()
    def create_entry():
        data = request.get_json(silent=True) or {}

        if current_user.role == "patient":
            patient_id = str(current_user.id)
        else:
            patient_id = data.get("patient_id")

        if not patient_id:
            return validation_error("patient_id is required")
        if not can_access_patient_data(current_user, patient_id):
            return api_error("Forbidden", 403)

        raw_value = data.get(spec.column)
        recorded_at = parse_datetime(data.get("recorded_at"))

        if raw_value is None:
            return validation_error(f"{spec.column} is required", spec.column)
        if not recorded_at:
            return validation_error(
                "Valid recorded_at datetime is required", "recorded_at"
            )

        value, err = validate_value_in_range(raw_value, spec)
        if err:
            return validation_error(err, spec.column)

        notes, err = clean_notes(data.get("notes"))
        if err:
            return validation_error(err, "notes")

        entry = model(
            patient_id=patient_id,
            recorded_at=recorded_at,
            notes=notes,
        )
        setattr(entry, spec.column, value)
        db.session.add(entry)
        db.session.commit()
        return jsonify(data=entry.to_dict()), 201

    @bp.route("/<uuid:entry_id>", methods=["GET"])
    @jwt_required()
    def get_entry(entry_id):
        entry = db.session.get(model, entry_id)
        if not entry:
            return api_error("Not found", 404)
        if not can_access_patient_data(current_user, entry.patient_id):
            return api_error("Forbidden", 403)
        return jsonify(data=entry.to_dict())

    @bp.route("/<uuid:entry_id>", methods=["PATCH"])
    @jwt_required()
    def update_entry(entry_id):
        entry = db.session.get(model, entry_id)
        if not entry:
            return api_error("Not found", 404)
        if not can_access_patient_data(current_user, entry.patient_id):
            return api_error("Forbidden", 403)

        data = request.get_json(silent=True) or {}
        if spec.column in data:
            value, err = validate_value_in_range(data[spec.column], spec)
            if err:
                return validation_error(err, spec.column)
            setattr(entry, spec.column, value)
        if "recorded_at" in data:
            dt = parse_datetime(data["recorded_at"])
            if not dt:
                return validation_error(
                    "Valid recorded_at datetime is required", "recorded_at"
                )
            entry.recorded_at = dt
        if "notes" in data:
            notes, err = clean_notes(data["notes"])
            if err:
                return validation_error(err, "notes")
            entry.notes = notes

        db.session.commit()
        return jsonify(data=entry.to_dict())

    @bp.route("/<uuid:entry_id>", methods=["DELETE"])
    @jwt_required()
    def delete_entry(entry_id):
        entry = db.session.get(model, entry_id)
        if not entry:
            return api_error("Not found", 404)
        if not can_access_patient_data(current_user, entry.patient_id):
            return api_error("Forbidden", 403)
        db.session.delete(entry)
        db.session.commit()
        return jsonify(message="Deleted")

    return bp
