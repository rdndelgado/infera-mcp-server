"""fact_subscription_snapshot / fact_subscription_events generator.

Two passes:
  1. build_lifecycles() — a random walk per customer: pick an initial plan,
     then repeatedly roll a gap-to-next-event and an upgrade/downgrade/
     cancellation (with a chance of reactivation after cancelling).
  2. apply_anomaly() — post-processing pass that forces a concentrated
     cancellation wave in ANOMALY_MONTH for subscriptions sitting on the
     anomaly product+tier, so "why did MRR/churn spike in March 2024" has a
     real, discoverable answer in fact_subscription_events.
"""

import random
from collections import defaultdict
from datetime import timedelta

from .config import (
    ANOMALY_FORCE_CHURN_PROB,
    ANOMALY_MONTH_END,
    ANOMALY_MONTH_START,
    ANOMALY_PLAN_TIER,
    ANOMALY_PRODUCT_ID,
    SEATS_BY_COMPANY_SIZE,
    WAREHOUSE_END,
)
from .util import round_money, weighted_choice

TIER_ORDER = ["Starter", "Growth", "Enterprise"]

SEGMENT_WEIGHTS = {
    "SMB": {"Starter": 0.70, "Growth": 0.25, "Enterprise": 0.05},
    "Mid-Market": {"Starter": 0.20, "Growth": 0.60, "Enterprise": 0.20},
    "Enterprise": {"Starter": 0.05, "Growth": 0.35, "Enterprise": 0.60},
}
PRODUCT_WEIGHTS = {"PROD-01": 0.5, "PROD-02": 0.3, "PROD-03": 0.2}
BILLING_INTERVAL_WEIGHTS = {"monthly": 0.7, "annual": 0.3}
EVENT_TYPE_WEIGHTS = {"upgrade": 0.40, "downgrade": 0.30, "cancellation": 0.30}
REACTIVATION_PROB = 0.15


def _plans_lookup(plans: list[dict]) -> dict:
    lookup = defaultdict(dict)
    for plan in plans:
        lookup[(plan["product_id"], plan["billing_interval"])][plan["tier"]] = plan
    return lookup


def _seats_for(company_size: str) -> int:
    low, high = SEATS_BY_COMPANY_SIZE[company_size]
    return random.randint(low, high)


def _monthly_equivalent(plan: dict) -> float:
    return plan["list_price"] if plan["billing_interval"] == "monthly" else plan["list_price"] / 12


def _mrr(plan: dict, seats: int) -> float:
    return round_money(_monthly_equivalent(plan) * seats)


def _pick_initial_plan(segment: str, lookup: dict) -> dict:
    product_id = weighted_choice(list(PRODUCT_WEIGHTS), list(PRODUCT_WEIGHTS.values()))
    billing_interval = weighted_choice(
        list(BILLING_INTERVAL_WEIGHTS), list(BILLING_INTERVAL_WEIGHTS.values())
    )
    weights = SEGMENT_WEIGHTS[segment]
    tier = weighted_choice(list(weights), list(weights.values()))
    return lookup[(product_id, billing_interval)][tier]


def _adjacent_plan(plan: dict, direction: str, lookup: dict) -> dict:
    idx = TIER_ORDER.index(plan["tier"])
    new_idx = idx + 1 if direction == "upgrade" else idx - 1
    if not (0 <= new_idx <= 2):
        new_idx = idx - 1 if direction == "upgrade" else idx + 1  # flip at boundary
    new_tier = TIER_ORDER[new_idx]
    return lookup[(plan["product_id"], plan["billing_interval"])][new_tier]


def _event_row(event_date, customer_id, subscription_id, event_type, prev_plan, new_plan, seats):
    prev_mrr = _mrr(prev_plan, seats) if prev_plan else None
    new_mrr = _mrr(new_plan, seats) if new_plan else 0.0
    if event_type == "cancellation":
        mrr_change = -prev_mrr
    else:
        mrr_change = round_money((new_mrr or 0) - (prev_mrr or 0))
    ref_plan = new_plan or prev_plan
    return {
        "date": event_date,
        "customer_id": customer_id,
        "product_id": ref_plan["product_id"],
        "plan_id": ref_plan["plan_id"],
        "subscription_id": subscription_id,
        "event_type": event_type,
        "previous_plan_id": prev_plan["plan_id"] if prev_plan else None,
        "new_plan_id": new_plan["plan_id"] if new_plan else None,
        "previous_mrr": prev_mrr,
        "new_mrr": new_mrr if event_type != "cancellation" else None,
        "mrr_change": mrr_change,
        "event_timestamp": event_date,
    }


def build_lifecycles(customers: list[dict], plans: list[dict]) -> dict:
    lookup = _plans_lookup(plans)
    subscriptions, segments, events = [], [], []
    customer_status = {}

    for customer in (c for c in customers if not c["is_prospect"]):
        seats = _seats_for(customer["company_size"])
        plan = _pick_initial_plan(customer["customer_segment"], lookup)
        start_date = customer["acquisition_date"] + timedelta(days=random.randint(0, 14))
        if start_date > WAREHOUSE_END:
            start_date = WAREHOUSE_END
        subscription_id = f"SUB-{customer['customer_id'][-5:]}"

        events.append(_event_row(start_date, customer["customer_id"], subscription_id, "new", None, plan, seats))
        initial_plan_id, initial_product_id, initial_mrr = plan["plan_id"], plan["product_id"], _mrr(plan, seats)

        current_start = start_date
        final_status, final_cancel_date = "active", None

        while True:
            gap_days = random.randint(60, 300)
            next_date = current_start + timedelta(days=gap_days)
            if next_date > WAREHOUSE_END:
                segments.append(
                    {
                        "subscription_id": subscription_id,
                        "customer_id": customer["customer_id"],
                        "start": current_start,
                        "end": WAREHOUSE_END,
                        "plan_id": plan["plan_id"],
                        "product_id": plan["product_id"],
                        "tier": plan["tier"],
                        "mrr": _mrr(plan, seats),
                    }
                )
                break

            segments.append(
                {
                    "subscription_id": subscription_id,
                    "customer_id": customer["customer_id"],
                    "start": current_start,
                    "end": next_date - timedelta(days=1),
                    "plan_id": plan["plan_id"],
                    "product_id": plan["product_id"],
                    "tier": plan["tier"],
                    "mrr": _mrr(plan, seats),
                }
            )

            event_type = weighted_choice(list(EVENT_TYPE_WEIGHTS), list(EVENT_TYPE_WEIGHTS.values()))

            if event_type == "cancellation":
                events.append(
                    _event_row(next_date, customer["customer_id"], subscription_id, "cancellation", plan, None, seats)
                )
                if random.random() < REACTIVATION_PROB:
                    reactivate_date = next_date + timedelta(days=random.randint(30, 120))
                    if reactivate_date <= WAREHOUSE_END:
                        events.append(
                            _event_row(
                                reactivate_date, customer["customer_id"], subscription_id,
                                "reactivation", None, plan, seats,
                            )
                        )
                        current_start = reactivate_date
                        continue
                final_status, final_cancel_date = "cancelled", next_date
                break
            else:
                new_plan = _adjacent_plan(plan, event_type, lookup)
                events.append(
                    _event_row(next_date, customer["customer_id"], subscription_id, event_type, plan, new_plan, seats)
                )
                plan = new_plan
                current_start = next_date

        subscriptions.append(
            {
                "subscription_id": subscription_id,
                "customer_id": customer["customer_id"],
                "seats": seats,
                "start_date": start_date,
                "final_status": final_status,
                "final_cancel_date": final_cancel_date,
                "initial_plan_id": initial_plan_id,
                "initial_product_id": initial_product_id,
                "initial_mrr": initial_mrr,
            }
        )
        customer_status[customer["customer_id"]] = "active" if final_status == "active" else "churned"

    return {
        "subscriptions": subscriptions,
        "segments": segments,
        "events": events,
        "customer_status": customer_status,
    }


def apply_anomaly(lifecycle: dict) -> None:
    """Mutates lifecycle in place: forces a churn wave in ANOMALY_MONTH for
    subscriptions on the anomaly product+tier."""
    subscriptions = {s["subscription_id"]: s for s in lifecycle["subscriptions"]}
    segments = lifecycle["segments"]
    events = lifecycle["events"]

    segs_by_sub = defaultdict(list)
    for seg in segments:
        segs_by_sub[seg["subscription_id"]].append(seg)
    events_by_sub = defaultdict(list)
    for evt in events:
        events_by_sub[evt["subscription_id"]].append(evt)

    for sub_id, sub_segments in segs_by_sub.items():
        sub_segments.sort(key=lambda s: s["start"])
        target = next(
            (
                s for s in sub_segments
                if s["product_id"] == ANOMALY_PRODUCT_ID
                and s["tier"] == ANOMALY_PLAN_TIER
                and s["start"] <= ANOMALY_MONTH_END
                and s["end"] >= ANOMALY_MONTH_START
            ),
            None,
        )
        if target is None or random.random() >= ANOMALY_FORCE_CHURN_PROB:
            continue

        window_start = max(target["start"], ANOMALY_MONTH_START)
        window_end = min(target["end"], ANOMALY_MONTH_END)
        span = max((window_end - window_start).days, 0)
        forced_date = window_start + timedelta(days=random.randint(0, span))

        target["end"] = forced_date - timedelta(days=1)
        for seg in list(sub_segments):
            if seg is not target and seg["start"] > forced_date:
                segments.remove(seg)
        if target["end"] < target["start"]:
            segments.remove(target)

        for evt in list(events_by_sub[sub_id]):
            if evt["date"] > forced_date:
                events.remove(evt)

        sub = subscriptions[sub_id]
        events.append(
            {
                "date": forced_date,
                "customer_id": sub["customer_id"],
                "product_id": target["product_id"],
                "plan_id": target["plan_id"],
                "subscription_id": sub_id,
                "event_type": "cancellation",
                "previous_plan_id": target["plan_id"],
                "new_plan_id": None,
                "previous_mrr": target["mrr"],
                "new_mrr": None,
                "mrr_change": -target["mrr"],
                "event_timestamp": forced_date,
            }
        )
        sub["final_status"] = "cancelled"
        sub["final_cancel_date"] = forced_date
        lifecycle["customer_status"][sub["customer_id"]] = "churned"


def expand_snapshot_rows(lifecycle: dict) -> list[dict]:
    """One row per subscription per active day (dead/cancelled gaps produce
    no rows), per fact_subscription_snapshot's grain."""
    subs_by_id = {s["subscription_id"]: s for s in lifecycle["subscriptions"]}
    rows = []
    for seg in lifecycle["segments"]:
        sub = subs_by_id[seg["subscription_id"]]
        d = seg["start"]
        while d <= seg["end"]:
            rows.append(
                {
                    "snapshot_date": d,
                    "customer_id": seg["customer_id"],
                    "product_id": seg["product_id"],
                    "plan_id": seg["plan_id"],
                    "subscription_id": seg["subscription_id"],
                    "subscription_status": "active",
                    "mrr": seg["mrr"],
                    "arr": round_money(seg["mrr"] * 12),
                    "quantity": sub["seats"],
                    "subscription_start_date": sub["start_date"],
                    "subscription_end_date": sub["final_cancel_date"],
                }
            )
            d += timedelta(days=1)
    return rows
