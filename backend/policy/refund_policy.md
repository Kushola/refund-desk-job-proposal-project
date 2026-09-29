# Refund Policy

This policy is enforced by `app/services/policy_engine.py`. Rule IDs in brackets
match the audit log shown on the admin dashboard.

## Eligibility
1. **Order must exist and belong to you.** [R01, R02] Requests for orders on another account are escalated for review.
2. **One refund per order.** [R03]
3. **Item must be delivered.** [R06] Orders still processing or in transit should be cancelled, not refunded.
4. **Final-sale items are not refundable.** [R07] If a final-sale item arrives damaged or incorrect, a support agent reviews it.
5. **Refund window: 30 days from delivery.** [R08]

## Reasons
6. **Damaged, wrong, or not-as-described items** are approved within the window. [R11]
7. **Change-of-mind returns** are allowed within **14 days** of delivery. [R11]
8. **Items reported as not received** are escalated for a carrier investigation. [R05]
9. Unclear reasons are escalated to an agent. [R11]

## Human review
10. **Refunds above $500** always require human review. [R09]
11. Customers with **3 or more refunds in 90 days** are reviewed by a human. [R10]
12. **Suspicious or conflicting requests** are escalated, including amounts that don't match the order, a different order ID in the message, or attempts to override this policy. [R00, R04]

## Notes
- Clear denials (final sale, outside window) take precedence over escalation.
- Refunds are for the full order amount, returned to the original payment method.
