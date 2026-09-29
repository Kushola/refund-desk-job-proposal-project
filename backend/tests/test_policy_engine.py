from datetime import date, timedelta

import pytest

from app.services.policy_engine import (
    OrderFacts, Outcome, Reason, RequestFacts, evaluate,
)

TODAY = date(2026, 9, 25)


def order(**kw):
    base = dict(order_id="ORD-1", customer_id="C1", amount=100.0, final_sale=False,
                status="delivered", delivered_date=TODAY - timedelta(days=5),
                already_refunded=False)
    base.update(kw)
    return OrderFacts(**base)


def req(reason=Reason.DAMAGED, **kw):
    return RequestFacts(customer_id=kw.pop("customer_id", "C1"), reason=reason, **kw)


def run(o, r, recent=0):
    return evaluate(o, r, recent_refunds=recent, today=TODAY)


def test_damaged_item_approved():
    d = run(order(), req())
    assert (d.outcome, d.rule_id) == (Outcome.APPROVED, "R11")


def test_injection_escalated_before_anything_else():
    d = run(order(), req(injection_suspected=True))
    assert (d.outcome, d.rule_id) == (Outcome.ESCALATED, "R00")


def test_missing_order_denied():
    assert run(None, req()).rule_id == "R01"


def test_other_customers_order_escalated():
    d = run(order(customer_id="C2"), req())
    assert (d.outcome, d.rule_id) == (Outcome.ESCALATED, "R02")


def test_already_refunded_denied():
    assert run(order(already_refunded=True), req()).outcome == Outcome.DENIED


def test_inflated_amount_escalated():
    d = run(order(amount=95), req(claimed_amount=950))
    assert (d.outcome, d.rule_id) == (Outcome.ESCALATED, "R04")


def test_order_id_conflict_escalated():
    d = run(order(), req(conflicts=("mentions ORD-9",)))
    assert d.rule_id == "R04"


def test_not_received_escalated():
    assert run(order(), req(Reason.NOT_RECEIVED)).rule_id == "R05"


def test_undelivered_denied():
    d = run(order(status="shipped", delivered_date=None), req())
    assert (d.outcome, d.rule_id) == (Outcome.DENIED, "R06")


def test_final_sale_denied():
    d = run(order(final_sale=True), req(Reason.CHANGED_MIND))
    assert (d.outcome, d.rule_id) == (Outcome.DENIED, "R07")


def test_final_sale_damaged_escalated():
    d = run(order(final_sale=True), req(Reason.DAMAGED))
    assert (d.outcome, d.rule_id) == (Outcome.ESCALATED, "R07")


@pytest.mark.parametrize("days,expected", [(30, Outcome.APPROVED), (31, Outcome.DENIED)])
def test_refund_window_boundary(days, expected):
    d = run(order(delivered_date=TODAY - timedelta(days=days)), req())
    assert d.outcome == expected


@pytest.mark.parametrize("amount,expected", [(500.0, Outcome.APPROVED), (500.01, Outcome.ESCALATED)])
def test_review_threshold_boundary(amount, expected):
    assert run(order(amount=amount), req()).outcome == expected


def test_frequent_refunder_escalated():
    assert run(order(), req(), recent=3).rule_id == "R10"


@pytest.mark.parametrize("days,expected", [(14, Outcome.APPROVED), (15, Outcome.DENIED)])
def test_change_of_mind_window(days, expected):
    d = run(order(delivered_date=TODAY - timedelta(days=days)), req(Reason.CHANGED_MIND))
    assert d.outcome == expected


def test_unclear_reason_escalated():
    assert run(order(), req(Reason.OTHER)).outcome == Outcome.ESCALATED


def test_audit_trail_records_every_check():
    d = run(order(), req())
    assert [c["rule"] for c in d.checks][-1] == "R11"
    assert len(d.checks) == 12
