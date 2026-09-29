from flask import Blueprint, abort, jsonify, request
from pydantic import ValidationError

from ..extensions import db
from ..models import RefundRequest
from ..schemas import RefundRequestIn
from ..services.refund_service import process_refund

bp = Blueprint("refunds", __name__)


@bp.post("/refund-requests")
def create_refund_request():
    try:
        payload = RefundRequestIn.model_validate(request.get_json(silent=True) or {})
    except ValidationError as exc:
        return jsonify({"error": "invalid_request", "details": exc.errors(include_url=False)}), 422
    try:
        record = process_refund(payload.customer_id, payload.order_id, payload.message)
    except LookupError as exc:
        return jsonify({"error": str(exc)}), 404
    return jsonify(record.to_dict()), 201


@bp.get("/refund-requests")
def list_refund_requests():
    q = RefundRequest.query
    outcome = request.args.get("outcome")
    if outcome:
        q = q.filter_by(outcome=outcome.upper())
    rows = q.order_by(RefundRequest.created_at.desc()).limit(100).all()
    return jsonify([r.to_dict() for r in rows])


@bp.get("/refund-requests/<int:request_id>")
def get_refund_request(request_id):
    record = db.session.get(RefundRequest, request_id)
    if record is None:
        abort(404, description="Refund request not found")
    return jsonify(record.to_dict())


@bp.get("/stats")
def stats():
    rows = db.session.query(RefundRequest.outcome, db.func.count()).group_by(RefundRequest.outcome)
    return jsonify({outcome: count for outcome, count in rows})
