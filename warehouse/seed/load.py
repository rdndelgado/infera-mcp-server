"""Loads generated seed data into the warehouse Postgres.

Truncates every table first (RESTART IDENTITY CASCADE), so reruns are
idempotent: same deterministic generation (seed=42) in, same warehouse
state out. Run as: python -m warehouse.seed.load
"""

from db.warehouse.client import get_connection
from utils.logger import get_logger
from warehouse.seed.generate_all import generate_all
from warehouse.seed.generators.util import date_key

logger = get_logger(__name__)

TRUNCATE_ORDER = [
    "fact_pipeline_snapshot",
    "fact_subscription_events",
    "fact_subscription_snapshot",
    "fact_sales",
    "dim_plan",
    "dim_product",
    "dim_customer",
    "dim_date",
]


def _truncate_all(cur) -> None:
    for table in TRUNCATE_ORDER:
        cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")


def _load_dim_date(cur, rows) -> None:
    with cur.copy(
        "COPY dim_date (date_key, date, day, day_of_week, day_name, week, "
        "month, month_name, quarter, year, is_month_start, is_month_end) FROM STDIN"
    ) as copy:
        for r in rows:
            copy.write_row(
                (
                    r["date_key"], r["date"], r["day"], r["day_of_week"], r["day_name"],
                    r["week"], r["month"], r["month_name"], r["quarter"], r["year"],
                    r["is_month_start"], r["is_month_end"],
                )
            )


def _load_dim_product(cur, rows) -> dict:
    cur.executemany(
        "INSERT INTO dim_product (product_id, product_name, product_category) "
        "VALUES (%(product_id)s, %(product_name)s, %(product_category)s)",
        rows,
    )
    cur.execute("SELECT product_id, product_key FROM dim_product")
    return dict(cur.fetchall())


def _load_dim_plan(cur, rows, product_key_by_id) -> dict:
    cur.executemany(
        "INSERT INTO dim_plan (plan_id, plan_name, product_key, billing_interval, list_price, currency) "
        "VALUES (%(plan_id)s, %(plan_name)s, %(product_key)s, %(billing_interval)s, %(list_price)s, %(currency)s)",
        [{**r, "product_key": product_key_by_id[r["product_id"]]} for r in rows],
    )
    cur.execute("SELECT plan_id, plan_key FROM dim_plan")
    return dict(cur.fetchall())


def _load_dim_customer(cur, rows) -> dict:
    cur.executemany(
        "INSERT INTO dim_customer (customer_id, customer_name, industry, company_size, country, "
        "customer_segment, acquisition_date, status) "
        "VALUES (%(customer_id)s, %(customer_name)s, %(industry)s, %(company_size)s, %(country)s, "
        "%(customer_segment)s, %(acquisition_date)s, %(status)s)",
        rows,
    )
    cur.execute("SELECT customer_id, customer_key FROM dim_customer")
    return dict(cur.fetchall())


def _load_fact_sales(cur, rows, customer_key_by_id, product_key_by_id, plan_key_by_id) -> None:
    cur.executemany(
        "INSERT INTO fact_sales (date_key, customer_key, product_key, plan_key, opportunity_id, "
        "deal_amount, contract_value, currency, sales_stage, sales_status, sales_rep, closed_at) "
        "VALUES (%(date_key)s, %(customer_key)s, %(product_key)s, %(plan_key)s, %(opportunity_id)s, "
        "%(deal_amount)s, %(contract_value)s, %(currency)s, %(sales_stage)s, %(sales_status)s, "
        "%(sales_rep)s, %(closed_at)s)",
        [
            {
                **r,
                "date_key": date_key(r["date"]),
                "customer_key": customer_key_by_id[r["customer_id"]],
                "product_key": product_key_by_id[r["product_id"]],
                "plan_key": plan_key_by_id[r["plan_id"]],
            }
            for r in rows
        ],
    )


def _load_fact_subscription_events(cur, rows, customer_key_by_id, product_key_by_id, plan_key_by_id) -> None:
    cur.executemany(
        "INSERT INTO fact_subscription_events (date_key, customer_key, product_key, plan_key, "
        "subscription_id, event_type, previous_plan_key, new_plan_key, previous_mrr, new_mrr, "
        "mrr_change, event_timestamp) "
        "VALUES (%(date_key)s, %(customer_key)s, %(product_key)s, %(plan_key)s, %(subscription_id)s, "
        "%(event_type)s, %(previous_plan_key)s, %(new_plan_key)s, %(previous_mrr)s, %(new_mrr)s, "
        "%(mrr_change)s, %(event_timestamp)s)",
        [
            {
                **r,
                "date_key": date_key(r["date"]),
                "customer_key": customer_key_by_id[r["customer_id"]],
                "product_key": product_key_by_id[r["product_id"]],
                "plan_key": plan_key_by_id[r["plan_id"]],
                "previous_plan_key": plan_key_by_id.get(r["previous_plan_id"]),
                "new_plan_key": plan_key_by_id.get(r["new_plan_id"]),
            }
            for r in rows
        ],
    )


def _load_fact_subscription_snapshot(cur, rows, customer_key_by_id, product_key_by_id, plan_key_by_id) -> None:
    with cur.copy(
        "COPY fact_subscription_snapshot (snapshot_date_key, customer_key, product_key, plan_key, "
        "subscription_id, subscription_status, mrr, arr, quantity, subscription_start_date, "
        "subscription_end_date) FROM STDIN"
    ) as copy:
        for r in rows:
            copy.write_row(
                (
                    date_key(r["snapshot_date"]),
                    customer_key_by_id[r["customer_id"]],
                    product_key_by_id[r["product_id"]],
                    plan_key_by_id[r["plan_id"]],
                    r["subscription_id"],
                    r["subscription_status"],
                    r["mrr"],
                    r["arr"],
                    r["quantity"],
                    r["subscription_start_date"],
                    r["subscription_end_date"],
                )
            )


def _load_fact_pipeline_snapshot(cur, rows, customer_key_by_id, product_key_by_id, plan_key_by_id) -> None:
    with cur.copy(
        "COPY fact_pipeline_snapshot (snapshot_date_key, customer_key, product_key, plan_key, "
        "opportunity_id, pipeline_stage, pipeline_status, amount, probability, weighted_amount, "
        "expected_close_date) FROM STDIN"
    ) as copy:
        for r in rows:
            copy.write_row(
                (
                    date_key(r["snapshot_date"]),
                    customer_key_by_id[r["customer_id"]],
                    product_key_by_id[r["product_id"]],
                    plan_key_by_id[r["plan_id"]],
                    r["opportunity_id"],
                    r["pipeline_stage"],
                    r["pipeline_status"],
                    r["amount"],
                    r["probability"],
                    r["weighted_amount"],
                    r["expected_close_date"],
                )
            )


def main() -> None:
    logger.info("Generating seed data (seed=42, deterministic)...")
    data = generate_all()

    logger.info("Connecting to warehouse and truncating tables...")
    with get_connection() as conn:
        with conn.cursor() as cur:
            _truncate_all(cur)

            _load_dim_date(cur, data["dim_dates"])
            product_key_by_id = _load_dim_product(cur, data["dim_products"])
            plan_key_by_id = _load_dim_plan(cur, data["dim_plans"], product_key_by_id)
            customer_key_by_id = _load_dim_customer(cur, data["dim_customers"])

            _load_fact_sales(cur, data["fact_sales"], customer_key_by_id, product_key_by_id, plan_key_by_id)
            _load_fact_subscription_events(
                cur, data["fact_subscription_events"], customer_key_by_id, product_key_by_id, plan_key_by_id
            )
            _load_fact_subscription_snapshot(
                cur, data["fact_subscription_snapshot"], customer_key_by_id, product_key_by_id, plan_key_by_id
            )
            _load_fact_pipeline_snapshot(
                cur, data["fact_pipeline_snapshot"], customer_key_by_id, product_key_by_id, plan_key_by_id
            )

        conn.commit()

    logger.info("Load complete.")
    logger.info(f"  dim_date: {len(data['dim_dates'])}")
    logger.info(f"  dim_product: {len(data['dim_products'])}")
    logger.info(f"  dim_plan: {len(data['dim_plans'])}")
    logger.info(f"  dim_customer: {len(data['dim_customers'])}")
    logger.info(f"  fact_sales: {len(data['fact_sales'])}")
    logger.info(f"  fact_subscription_events: {len(data['fact_subscription_events'])}")
    logger.info(f"  fact_subscription_snapshot: {len(data['fact_subscription_snapshot'])}")
    logger.info(f"  fact_pipeline_snapshot: {len(data['fact_pipeline_snapshot'])}")


if __name__ == "__main__":
    main()
