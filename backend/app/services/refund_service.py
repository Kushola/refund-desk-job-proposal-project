"""Orchestrates one refund request: screen -> extract -> decide -> reply -> persist."""
from datetime import date, datetime, timedelta, timezone

from flask import current_app

from ..extensions import db
from ..models import Customer, Order, RefundRequest
from . import guardrails
from .llm_client import LLMClient
from .policy_engine import OrderFacts, Outcome, RequestFacts, evaluate


def _llm() -> LLMClient:
    cfg = current_app.config
    return LLMClient(cfg["LLM_API_KEY"], cfg["LLM_MODEL"])


def recent_refund_count(customer: Customer) -> int:
    since = datetime.now(timezone.utc) - timedelta(days=90)
    approved = RefundRequest.query.filter(
        RefundRequest.customer_id == customer.id,
        RefundRequest.outcome == Outcome.APPROVED.value,
        RefundRequest.created_at >= since,
    ).count()
    return (customer.prior_refunds_90d or 0) + approved


def process_refund(customer_id: str, order_id: str, message: str, today: date | None = None):
    today = today or date.today()
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        raise LookupError("Unknown customer")

    screened = guardrails.screen(message)
    llm = _llm()
    intent, llm_flags = llm.extract_intent(screened.text)
    flags = screened.flags + llm_flags

    conflicts = []
    if intent.mentioned_order_id and intent.mentioned_order_id != order_id.upper():
        conflicts.append(
            f"Message mentions {intent.mentioned_order_id} but {order_id} was selected.")

    order = db.session.get(Order, order_id.upper())
    order_facts = None
    if order is not None:
        order_facts = OrderFacts(
            order_id=order.id,
            customer_id=order.customer_id,
            amount=order.amount,
            final_sale=order.final_sale,
            status=order.status,
            delivered_date=order.delivered_date,
            already_refunded=order.refunded,
        )

    decision = evaluate(
        order_facts,
        RequestFacts(
            customer_id=customer.id,
            reason=intent.reason,
            claimed_amount=intent.claimed_amount,
            injection_suspected=screened.injection_suspected,
            conflicts=tuple(conflicts),
        ),
        recent_refunds=recent_refund_count(customer),
        today=today,
    )

    reply = llm.draft_reply(decision, customer.name.split()[0], order.item_name if order else None)

    record = RefundRequest(
        customer_id=customer.id,
        order_id=order.id if order else order_id,
        message=screened.text,
        extracted=intent.model_dump(mode="json"),
        outcome=decision.outcome.value,
        rule_id=decision.rule_id,
        summary=decision.summary,
        audit=decision.checks,
        flags=flags,
        customer_reply=reply,
        decided_by="llm+rules" if llm.enabled else "rules-only",
    )
    if decision.outcome == Outcome.APPROVED and order is not None:
        order.refunded = True
    db.session.add(record)
    db.session.commit()
    return record
