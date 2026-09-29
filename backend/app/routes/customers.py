from flask import Blueprint, abort, jsonify

from ..extensions import db
from ..models import Customer, Order

bp = Blueprint("customers", __name__)


@bp.get("/customers")
def list_customers():
    return jsonify([c.to_dict() for c in Customer.query.order_by(Customer.id).all()])


@bp.get("/customers/<customer_id>/orders")
def customer_orders(customer_id):
    if db.session.get(Customer, customer_id) is None:
        abort(404, description="Customer not found")
    orders = Order.query.filter_by(customer_id=customer_id).order_by(Order.order_date.desc())
    return jsonify([o.to_dict() for o in orders])
