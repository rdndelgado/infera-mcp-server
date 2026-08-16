"""Business logic for get_customer_metrics / get_top_customers (PRD_V2 §10.3)."""

from datetime import date

from db.warehouse import queries
from db.warehouse.client import get_connection
from schemas.customer import CustomerMetrics, TopCustomer
from utils.validators import validate_period


def get_customer_metrics(period_start: date, period_end: date) -> CustomerMetrics:
    validate_period(period_start, period_end)
    with get_connection() as conn:
        active = queries.get_active_customers_count(conn, period_end)
        previous_active = queries.get_active_customers_count(conn, period_start)
        new = queries.get_new_customers_count(conn, period_start, period_end)
        churned = queries.get_churned_customers_count(conn, period_start, period_end)

    growth_rate = 0.0 if previous_active == 0 else round((active - previous_active) / previous_active * 100, 2)

    return CustomerMetrics(
        active_customers=active,
        new_customers=new,
        churned_customers=churned,
        customer_growth_rate=growth_rate,
    )


def get_top_customers(as_of_date: date, limit: int) -> list[TopCustomer]:
    if not 1 <= limit <= 50:
        raise ValueError(f"limit must be between 1 and 50, got {limit}")
    with get_connection() as conn:
        rows = queries.get_top_customers(conn, as_of_date, limit)
    return [TopCustomer(customer_id=r["customer_id"], customer_name=r["customer_name"], mrr=float(r["mrr"])) for r in rows]
