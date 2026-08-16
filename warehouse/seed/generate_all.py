"""Orchestrates the seed generators into one raw-data bundle for load.py.

Run order matters: subscriptions depend on customers+plans, and
sales/pipeline depend on subscriptions (a won customer's deal is tied to
their real starting plan/MRR).
"""

from .generators import products_plans, sales_pipeline
from .generators import customers as customers_gen
from .generators import dates as dates_gen
from .generators import subscriptions as subs_gen
from .generators.util import seed_all


def generate_all() -> dict:
    seed_all()

    dim_dates = dates_gen.generate_dates()
    dim_products = products_plans.generate_products()
    dim_plans = products_plans.generate_plans()
    dim_customers = customers_gen.generate_customers()

    lifecycle = subs_gen.build_lifecycles(dim_customers, dim_plans)
    subs_gen.apply_anomaly(lifecycle)
    fact_subscription_snapshot = subs_gen.expand_snapshot_rows(lifecycle)

    fact_sales, fact_pipeline_snapshot = sales_pipeline.generate_sales_and_pipeline(
        dim_customers, dim_plans, lifecycle
    )

    for customer in dim_customers:
        if not customer["is_prospect"]:
            customer["status"] = lifecycle["customer_status"].get(customer["customer_id"], "active")

    return {
        "dim_dates": dim_dates,
        "dim_products": dim_products,
        "dim_plans": dim_plans,
        "dim_customers": dim_customers,
        "fact_subscription_events": lifecycle["events"],
        "fact_subscription_snapshot": fact_subscription_snapshot,
        "fact_sales": fact_sales,
        "fact_pipeline_snapshot": fact_pipeline_snapshot,
    }
