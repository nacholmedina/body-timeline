from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

from app.extensions import db
from app.models.weigh_in import WeighIn
from app.services.body_metrics import (
    apply_body_metrics,
    serialize_body_metrics,
)
from app.services.rbac import can_access_patient_data, get_accessible_patient_ids
from app.utils.errors import validation_error, api_error
from app.utils.validators import parse_datetime, get_pagination_params

bp = Blueprint("weigh_ins", __name__)


def _serialize(wi, *, with_body_metrics=False):
    data = wi.to_dict()
    if with_body_metrics:
        data["body_metrics"] = serialize_body_metrics(wi.patient_id, wi.recorded_at)
    return data


@bp.route("", methods=["GET"])
@jwt_required()
def list_weigh_ins():
    patient_ids = get_accessible_patient_ids(current_user)
    query = WeighIn.query

    if patient_ids is not None:
        query = query.filter(WeighIn.patient_id.in_(patient_ids))

    pid = request.args.get("patient_id")
    if pid:
        if not can_access_patient_data(current_user, pid):
            return api_error("Forbidden", 403)
        query = query.filter_by(patient_id=pid)

    date_from = parse_datetime(request.args.get("from"))
    date_to = parse_datetime(request.args.get("to"))
    if date_from:
        query = query.filter(WeighIn.recorded_at >= date_from)
    if date_to:
        query = query.filter(WeighIn.recorded_at <= date_to)

    query = query.order_by(WeighIn.recorded_at.desc())
    page, limit, offset = get_pagination_params(request.args)
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return jsonify(data=[w.to_dict() for w in items], page=page, limit=limit, total=total)


@bp.route("", methods=["POST"])
@jwt_required()
def create_weigh_in():
    data = request.get_json(silent=True) or {}

    if current_user.role == "patient":
        patient_id = str(current_user.id)
    else:
        patient_id = data.get("patient_id")

    if not patient_id:
        return validation_error("patient_id is required")
    if not can_access_patient_data(current_user, patient_id):
        return api_error("Forbidden", 403)

    weight_kg = data.get("weight_kg")
    recorded_at = parse_datetime(data.get("recorded_at"))

    if weight_kg is None:
        return validation_error("weight_kg is required", "weight_kg")
    if not recorded_at:
        return validation_error("Valid recorded_at datetime is required", "recorded_at")

    try:
        weight_kg = float(weight_kg)
    except (ValueError, TypeError):
        return validation_error("weight_kg must be a number", "weight_kg")

    weigh_in = WeighIn(
        patient_id=patient_id,
        weight_kg=weight_kg,
        recorded_at=recorded_at,
        notes=data.get("notes"),
    )
    db.session.add(weigh_in)

    # Optional bulk body-metrics payload — handled in the same transaction.
    body_payload = data.get("body_metrics")
    if isinstance(body_payload, dict):
        db.session.flush()  # need patient_id resolved before metric inserts (it already is here, but flush keeps order obvious)
        err, field = apply_body_metrics(patient_id, body_payload, recorded_at)
        if err:
            db.session.rollback()
            return validation_error(err, field)

    db.session.commit()
    return jsonify(data=_serialize(weigh_in, with_body_metrics=True)), 201


@bp.route("/<uuid:weigh_in_id>", methods=["GET"])
@jwt_required()
def get_weigh_in(weigh_in_id):
    wi = db.session.get(WeighIn, weigh_in_id)
    if not wi:
        return api_error("Weigh-in not found", 404)
    if not can_access_patient_data(current_user, wi.patient_id):
        return api_error("Forbidden", 403)
    include_body = request.args.get("include") == "body_metrics"
    return jsonify(data=_serialize(wi, with_body_metrics=include_body))


@bp.route("/<uuid:weigh_in_id>", methods=["PATCH"])
@jwt_required()
def update_weigh_in(weigh_in_id):
    wi = db.session.get(WeighIn, weigh_in_id)
    if not wi:
        return api_error("Weigh-in not found", 404)
    if not can_access_patient_data(current_user, wi.patient_id):
        return api_error("Forbidden", 403)

    data = request.get_json(silent=True) or {}
    old_recorded_at = wi.recorded_at

    if "weight_kg" in data:
        try:
            wi.weight_kg = float(data["weight_kg"])
        except (ValueError, TypeError):
            return validation_error("weight_kg must be a number", "weight_kg")
    if "recorded_at" in data:
        dt = parse_datetime(data["recorded_at"])
        if not dt:
            return validation_error("Valid recorded_at datetime is required", "recorded_at")
        wi.recorded_at = dt
    if "notes" in data:
        wi.notes = data["notes"]

    raw_body = data.get("body_metrics")
    body_payload = raw_body if isinstance(raw_body, dict) else {}
    moved = old_recorded_at != wi.recorded_at

    # Run the helper if either the client sent metric instructions OR the
    # weigh-in's recorded_at moved (so existing linked rows follow along).
    if body_payload or moved:
        err, field = apply_body_metrics(
            wi.patient_id, body_payload, wi.recorded_at, old_recorded_at=old_recorded_at
        )
        if err:
            db.session.rollback()
            return validation_error(err, field)

    db.session.commit()
    return jsonify(data=_serialize(wi, with_body_metrics=True))


@bp.route("/<uuid:weigh_in_id>", methods=["DELETE"])
@jwt_required()
def delete_weigh_in(weigh_in_id):
    wi = db.session.get(WeighIn, weigh_in_id)
    if not wi:
        return api_error("Weigh-in not found", 404)
    if not can_access_patient_data(current_user, wi.patient_id):
        return api_error("Forbidden", 403)

    db.session.delete(wi)
    db.session.commit()
    return jsonify(message="Weigh-in deleted")
