"""15 customers with orders designed to hit every policy rule.

Dates are relative to today so the demo scenarios stay valid whenever it runs.
"""
from datetime import date, timedelta

from .extensions import db
from .models import Customer, Order

# (id, name, email, prior_refunds_90d)
CUSTOMERS = [
    ("CUST-001", "Amara Okafor", "amara@example.com", 0),
    ("CUST-002", "James Carter", "james@example.com", 0),
    ("CUST-003", "Priya Sharma", "priya@example.com", 0),
    ("CUST-004", "Liam Chen", "liam@example.com", 0),
    ("CUST-005", "Fatima Bello", "fatima@example.com", 4),
    ("CUST-006", "Noah Williams", "noah@example.com", 0),
    ("CUST-007", "Chloe Martin", "chloe@example.com", 1),
    ("CUST-008", "Tunde Adeyemi", "tunde@example.com", 0),
    ("CUST-009", "Sofia Rossi", "sofia@example.com", 0),
    ("CUST-010", "Ethan Brooks", "ethan@example.com", 0),
    ("CUST-011", "Zainab Musa", "zainab@example.com", 0),
    ("CUST-012", "Oliver Grant", "oliver@example.com", 1),
    ("CUST-013", "Mei Tanaka", "mei@example.com", 0),
    ("CUST-014", "David Mensah", "david@example.com", 2),
    ("CUST-015", "Grace Eze", "grace@example.com", 0),
]

# (id, customer, item, category, amount, final_sale, status, ordered_days_ago, delivered_days_ago, refunded)
# Comment = the demo scenario it exercises.
ORDERS = [
    ("ORD-1001", "CUST-001", "Wireless Headphones", "Electronics", 89.99, False, "delivered", 9, 5, False),   # damaged -> APPROVED
    ("ORD-1002", "CUST-001", "Leather Jacket", "Apparel", 120.00, True, "delivered", 14, 10, False),        # final sale -> DENIED
    ("ORD-1003", "CUST-002", "Laptop Pro 14", "Electronics", 1299.00, False, "delivered", 10, 7, False),    # > $500 -> ESCALATED
    ("ORD-1004", "CUST-003", "Blender", "Kitchen", 65.00, False, "delivered", 50, 45, False),               # too old -> DENIED
    ("ORD-1005", "CUST-004", "Running Sneakers", "Footwear", 140.00, True, "delivered", 6, 3, False),       # final sale + damaged -> ESCALATED
    ("ORD-1006", "CUST-005", "Summer Dress", "Apparel", 75.00, False, "delivered", 9, 6, False),            # frequent refunder -> ESCALATED
    ("ORD-1007", "CUST-006", "Phone Case", "Accessories", 25.00, False, "shipped", 3, None, False),         # not delivered -> DENIED
    ("ORD-1008", "CUST-007", "Coffee Maker", "Kitchen", 210.00, False, "delivered", 16, 12, True),          # already refunded -> DENIED
    ("ORD-1009", "CUST-008", "27in Monitor", "Electronics", 349.00, False, "delivered", 5, 2, False),       # wrong item -> APPROVED
    ("ORD-1010", "CUST-009", "Smart Watch", "Electronics", 520.00, False, "delivered", 7, 4, False),        # just over $500 -> ESCALATED
    ("ORD-1011", "CUST-010", "Travel Backpack", "Bags", 60.00, False, "delivered", 24, 20, False),          # changed mind day 20 -> DENIED
    ("ORD-1012", "CUST-011", "Desk Lamp", "Home", 45.00, False, "delivered", 11, 8, False),                 # changed mind day 8 -> APPROVED
    ("ORD-1013", "CUST-012", "Gaming Chair", "Furniture", 280.00, False, "delivered", 30, 25, False),       # damaged day 25 -> APPROVED
    ("ORD-1014", "CUST-012", "Mechanical Keyboard", "Electronics", 95.00, False, "delivered", 4, 1, False), # amount-mismatch demo
    ("ORD-1015", "CUST-013", "Skincare Set", "Beauty", 55.00, True, "delivered", 5, 2, False),              # final sale -> DENIED
    ("ORD-1016", "CUST-014", "Bluetooth Speaker", "Electronics", 180.00, False, "delivered", 13, 9, False), # not received claim -> ESCALATED
    ("ORD-1017", "CUST-015", "Tablet 10in", "Electronics", 499.00, False, "delivered", 33, 29, False),      # boundary: $499, day 29 -> APPROVED if damaged
    ("ORD-1018", "CUST-015", "USB-C Cable", "Accessories", 15.00, False, "delivered", 65, 60, False),       # too old -> DENIED
]


def seed_database(today: date | None = None):
    today = today or date.today()
    for cid, name, email, prior in CUSTOMERS:
        db.session.add(Customer(id=cid, name=name, email=email, prior_refunds_90d=prior))
    for oid, cid, item, cat, amt, fs, status, ordered, delivered, refunded in ORDERS:
        db.session.add(Order(
            id=oid, customer_id=cid, item_name=item, category=cat, amount=amt,
            final_sale=fs, status=status,
            order_date=today - timedelta(days=ordered),
            delivered_date=today - timedelta(days=delivered) if delivered is not None else None,
            refunded=refunded,
        ))
    db.session.commit()
