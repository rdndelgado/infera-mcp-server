"""fact_sales / fact_pipeline_snapshot generator.

Every "won" customer's deal is tied to the real initial plan/MRR their
subscription started at (from subscriptions.build_lifecycles output), so
deal_amount/contract_value line up with what they're actually paying.
"Lost" deals belong to prospect-only customers and use a hypothetical
plan estimate since no subscription ever happened.

A quarter of all lost deals are forced to close within ANOMALY_MONTH, so
win rate visibly dips that month alongside the churn spike in subscriptions.py.
"""

import random
from datetime import datetime, timedelta

from .config import ANOMALY_LOST_CONCENTRATION, ANOMALY_MONTH_END, ANOMALY_MONTH_START, SALES_REPS, WAREHOUSE_END, WAREHOUSE_START
from .subscriptions import _mrr, _pick_initial_plan, _plans_lookup, _seats_for
from .util import round_money

STAGES = ["Prospecting", "Qualification", "Proposal", "Negotiation"]
STAGE_PROBABILITY = {"Prospecting": 10, "Qualification": 35, "Proposal": 60, "Negotiation": 85}


def _random_time(d) -> datetime:
    return datetime(d.year, d.month, d.day, random.randint(8, 18), random.randint(0, 59))


def _random_window_date():
    span = (WAREHOUSE_END - WAREHOUSE_START).days
    return WAREHOUSE_START + timedelta(days=random.randint(0, span))


def _stage_for_progress(fraction: float) -> str:
    idx = min(int(fraction * len(STAGES)), len(STAGES) - 1)
    return STAGES[idx]


def generate_sales_and_pipeline(customers: list[dict], plans: list[dict], lifecycle: dict) -> tuple[list[dict], list[dict]]:
    lookup = _plans_lookup(plans)
    subs_by_customer = {s["customer_id"]: s for s in lifecycle["subscriptions"]}

    fact_sales, pipeline_snapshots = [], []

    for customer in customers:
        if customer["is_prospect"]:
            plan = _pick_initial_plan(customer["customer_segment"], lookup)
            seats = _seats_for(customer["company_size"])
            contract_value = round_money(_mrr(plan, seats) * 12)
            status = "lost"

            if random.random() < ANOMALY_LOST_CONCENTRATION:
                span = (ANOMALY_MONTH_END - ANOMALY_MONTH_START).days
                closed_date = ANOMALY_MONTH_START + timedelta(days=random.randint(0, span))
            else:
                closed_date = _random_window_date()
        else:
            sub = subs_by_customer[customer["customer_id"]]
            plan = next(p for p in plans if p["plan_id"] == sub["initial_plan_id"])
            seats = sub["seats"]
            contract_value = round_money(sub["initial_mrr"] * 12)
            status = "won"
            closed_date = sub["start_date"] - timedelta(days=random.randint(2, 10))
            if closed_date < WAREHOUSE_START:
                closed_date = WAREHOUSE_START

        opportunity_id = f"OPP-{customer['customer_id']}"
        cycle_days = random.randint(20, 70)
        created_date = closed_date - timedelta(days=cycle_days)
        if created_date < WAREHOUSE_START:
            created_date = WAREHOUSE_START
            cycle_days = max((closed_date - created_date).days, 1)

        fact_sales.append(
            {
                "date": closed_date,
                "customer_id": customer["customer_id"],
                "product_id": plan["product_id"],
                "plan_id": plan["plan_id"],
                "opportunity_id": opportunity_id,
                "deal_amount": contract_value,
                "contract_value": contract_value,
                "currency": "USD",
                "sales_stage": "Closed Won" if status == "won" else "Closed Lost",
                "sales_status": status,
                "sales_rep": random.choice(SALES_REPS),
                "closed_at": _random_time(closed_date),
            }
        )

        d = created_date
        while d < closed_date:
            fraction = (d - created_date).days / cycle_days
            stage = _stage_for_progress(fraction)
            probability = STAGE_PROBABILITY[stage]
            pipeline_snapshots.append(
                {
                    "snapshot_date": d,
                    "customer_id": customer["customer_id"],
                    "product_id": plan["product_id"],
                    "plan_id": plan["plan_id"],
                    "opportunity_id": opportunity_id,
                    "pipeline_stage": stage,
                    "pipeline_status": "open",
                    "amount": contract_value,
                    "probability": probability,
                    "weighted_amount": round_money(contract_value * probability / 100),
                    "expected_close_date": closed_date,
                }
            )
            d += timedelta(days=1)

    return fact_sales, pipeline_snapshots
