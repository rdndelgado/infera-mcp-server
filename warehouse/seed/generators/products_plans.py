"""dim_product / dim_plan generators.

Pricing is per-seat/month; annual plans are 10x the monthly price (2 months
free), so a subscription's MRR is always (monthly-equivalent price * seats).
"""

from .util import round_money

PRODUCTS = [
    {"product_id": "PROD-01", "product_name": "Core Platform", "product_category": "Platform"},
    {"product_id": "PROD-02", "product_name": "Analytics Suite", "product_category": "Analytics"},
    {"product_id": "PROD-03", "product_name": "Integrations Hub", "product_category": "Integrations"},
]

TIERS = [
    ("Starter", 49),
    ("Growth", 149),
    ("Enterprise", 349),
]


def generate_products() -> list[dict]:
    return list(PRODUCTS)


def generate_plans() -> list[dict]:
    rows = []
    for product in PRODUCTS:
        for tier_name, monthly_price in TIERS:
            rows.append(
                {
                    "plan_id": f"PLAN-{product['product_id'][-2:]}-{tier_name[:2].upper()}-MO",
                    "plan_name": f"{product['product_name']} {tier_name} (Monthly)",
                    "product_id": product["product_id"],
                    "tier": tier_name,
                    "billing_interval": "monthly",
                    "list_price": round_money(monthly_price),
                    "currency": "USD",
                }
            )
            rows.append(
                {
                    "plan_id": f"PLAN-{product['product_id'][-2:]}-{tier_name[:2].upper()}-YR",
                    "plan_name": f"{product['product_name']} {tier_name} (Annual)",
                    "product_id": product["product_id"],
                    "tier": tier_name,
                    "billing_interval": "annual",
                    "list_price": round_money(monthly_price * 10),
                    "currency": "USD",
                }
            )
    return rows
