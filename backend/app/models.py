from datetime import datetime, timezone

from .extensions import db


def utcnow():
    return datetime.now(timezone.utc)


class Customer(db.Model):
    id = db.Column(db.String(20), primary_key=True)  # e.g. CUST-001
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False, unique=True)
    prior_refunds_90d = db.Column(db.Integer, default=0)  # history from before this system
    orders = db.relationship("Order", backref="customer", lazy=True)

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email}


class Order(db.Model):
    id = db.Column(db.String(20), primary_key=True)  # e.g. ORD-1001
    customer_id = db.Column(db.String(20), db.ForeignKey("customer.id"), nullable=False)
    item_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    final_sale = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(20), nullable=False)  # processing | shipped | delivered
    order_date = db.Column(db.Date, nullable=False)
    delivered_date = db.Column(db.Date, nullable=True)
    refunded = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "item_name": self.item_name,
            "category": self.category,
            "amount": self.amount,
            "final_sale": self.final_sale,
            "status": self.status,
            "order_date": self.order_date.isoformat(),
            "delivered_date": self.delivered_date.isoformat() if self.delivered_date else None,
            "refunded": self.refunded,
        }


class RefundRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.String(20), db.ForeignKey("customer.id"), nullable=False)
    order_id = db.Column(db.String(20), nullable=True)
    message = db.Column(db.Text, nullable=False)
    extracted = db.Column(db.JSON)          # what the LLM (or fallback) pulled from the message
    outcome = db.Column(db.String(20))      # APPROVED | DENIED | ESCALATED
    rule_id = db.Column(db.String(10))      # the policy rule that decided it
    summary = db.Column(db.Text)
    audit = db.Column(db.JSON)              # every check the engine ran
    flags = db.Column(db.JSON)              # guardrail flags
    customer_reply = db.Column(db.Text)
    decided_by = db.Column(db.String(20))   # "llm+rules" | "rules-only"
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "order_id": self.order_id,
            "message": self.message,
            "extracted": self.extracted,
            "outcome": self.outcome,
            "rule_id": self.rule_id,
            "summary": self.summary,
            "audit": self.audit,
            "flags": self.flags,
            "customer_reply": self.customer_reply,
            "decided_by": self.decided_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
