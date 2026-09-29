"""
Deterministic refund policy engine.

This is the ONLY component allowed to decide a refund outcome.
It is pure (no DB, no LLM, no I/O) so it is easy to test and to audit.
The LLM only supplies a *reason category*; every number and date used here
comes from the database, never from the customer's text.

Rule precedence (first match wins):
  R00 guardrail flag         -> ESCALATED
  R01 order not found        -> DENIED
  R02 order not owned        -> ESCALATED
  R03 already refunded       -> DENIED
  R04 conflicting claims     -> ESCALATED
  R05 item not received      -> ESCALATED
  R06 not yet delivered      -> DENIED
  R07 final sale             -> DENIED (ESCALATED if damaged/wrong)
  R08 outside refund window  -> DENIED
  R09 amount over threshold  -> ESCALATED
  R10 too many recent refunds-> ESCALATED
  R11 reason check           -> APPROVED / DENIED / ESCALATED
"""
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class Outcome(str, Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    ESCALATED = "ESCALATED"


class Reason(str, Enum):
    DAMAGED = "damaged"
    WRONG_ITEM = "wrong_item"
    NOT_AS_DESCRIBED = "not_as_described"
    NOT_RECEIVED = "not_received"
    CHANGED_MIND = "changed_mind"
    OTHER = "other"


DEFECT_REASONS = {Reason.DAMAGED, Reason.WRONG_ITEM, Reason.NOT_AS_DESCRIBED}


@dataclass(frozen=True)
class PolicyConfig:
    refund_window_days: int = 30
    change_of_mind_window_days: int = 14
    human_review_threshold: float = 500.0
    max_recent_refunds: int = 3          # in the last 90 days
    amount_tolerance: float = 0.01


@dataclass(frozen=True)
class OrderFacts:
    order_id: str
    customer_id: str
    amount: float
    final_sale: bool
    status: str                      # processing | shipped | delivered
    delivered_date: Optional[date]
    already_refunded: bool


@dataclass(frozen=True)
class RequestFacts:
    customer_id: str
    reason: Reason
    claimed_amount: Optional[float] = None
    injection_suspected: bool = False
    conflicts: tuple = ()            # e.g. ("message mentions ORD-1099, selected ORD-1001",)


@dataclass
class Decision:
    outcome: Outcome
    rule_id: str
    summary: str
    checks: list = field(default_factory=list)

    def to_dict(self):
        return {
            "outcome": self.outcome.value,
            "rule_id": self.rule_id,
            "summary": self.summary,
            "checks": self.checks,
        }


class _Trail:
    def __init__(self):
        self.checks = []

    def ok(self, rule, detail):
        self.checks.append({"rule": rule, "passed": True, "detail": detail})

    def stop(self, rule, outcome, summary):
        self.checks.append({"rule": rule, "passed": False, "detail": summary})
        return Decision(outcome, rule, summary, self.checks)


def evaluate(
    order: Optional[OrderFacts],
    req: RequestFacts,
    recent_refunds: int,
    today: date,
    cfg: PolicyConfig = PolicyConfig(),
) -> Decision:
    t = _Trail()

    if req.injection_suspected:
        return t.stop("R00", Outcome.ESCALATED,
                      "Message contains possible policy-bypass or prompt-injection content.")
    t.ok("R00", "No guardrail flags.")

    if order is None:
        return t.stop("R01", Outcome.DENIED, "No matching order was found.")
    t.ok("R01", f"Order {order.order_id} found.")

    if order.customer_id != req.customer_id:
        return t.stop("R02", Outcome.ESCALATED,
                      "Order does not belong to the requesting customer.")
    t.ok("R02", "Order belongs to customer.")

    if order.already_refunded:
        return t.stop("R03", Outcome.DENIED, "This order has already been refunded.")
    t.ok("R03", "Order not previously refunded.")

    conflicts = list(req.conflicts)
    if req.claimed_amount is not None and req.claimed_amount > order.amount + cfg.amount_tolerance:
        conflicts.append(
            f"Claimed ${req.claimed_amount:.2f} exceeds order total ${order.amount:.2f}.")
    if conflicts:
        return t.stop("R04", Outcome.ESCALATED, "Conflicting details: " + " ".join(conflicts))
    t.ok("R04", "No conflicting details.")

    if req.reason == Reason.NOT_RECEIVED:
        return t.stop("R05", Outcome.ESCALATED,
                      "Customer reports item not received; needs carrier investigation.")
    t.ok("R05", "Not a missing-delivery claim.")

    if order.status != "delivered" or order.delivered_date is None:
        return t.stop("R06", Outcome.DENIED,
                      f"Order is '{order.status}', not delivered; use cancellation instead.")
    t.ok("R06", "Order delivered.")

    if order.final_sale:
        if req.reason in DEFECT_REASONS:
            return t.stop("R07", Outcome.ESCALATED,
                          "Final-sale item reported defective or incorrect; needs human review.")
        return t.stop("R07", Outcome.DENIED, "Final-sale items are not eligible for refunds.")
    t.ok("R07", "Not a final-sale item.")

    days = (today - order.delivered_date).days
    if days > cfg.refund_window_days:
        return t.stop("R08", Outcome.DENIED,
                      f"Delivered {days} days ago; refund window is {cfg.refund_window_days} days.")
    t.ok("R08", f"Delivered {days} days ago, within window.")

    if order.amount > cfg.human_review_threshold:
        return t.stop("R09", Outcome.ESCALATED,
                      f"Refund of ${order.amount:.2f} exceeds ${cfg.human_review_threshold:.0f}; "
                      "requires human review.")
    t.ok("R09", "Amount under review threshold.")

    if recent_refunds >= cfg.max_recent_refunds:
        return t.stop("R10", Outcome.ESCALATED,
                      f"Customer has {recent_refunds} refunds in the last 90 days.")
    t.ok("R10", "Refund frequency normal.")

    if req.reason in DEFECT_REASONS:
        return t.stop("R11", Outcome.APPROVED,
                      f"Eligible: item reported as {req.reason.value.replace('_', ' ')}.")
    if req.reason == Reason.CHANGED_MIND:
        if days <= cfg.change_of_mind_window_days:
            return t.stop("R11", Outcome.APPROVED, "Change-of-mind return within 14 days.")
        return t.stop("R11", Outcome.DENIED,
                      f"Change-of-mind returns are allowed within "
                      f"{cfg.change_of_mind_window_days} days; this is day {days}.")
    return t.stop("R11", Outcome.ESCALATED, "Reason unclear; routed to a support agent.")
