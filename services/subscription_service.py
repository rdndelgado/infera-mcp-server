"""Business logic for get_subscription_metrics / get_churn_metrics (PRD_V2 §10.4).
Churn rate / revenue churn rate / NRR formulas per §9. New-customer MRR is
intentionally excluded from NRR per §9.
"""

from datetime import date

from db.warehouse import queries
from db.warehouse.client import get_connection
from schemas.subscription import ChurnMetrics, SubscriptionMetrics
from utils.validators import validate_period


def get_subscription_metrics(period_start: date, period_end: date) -> SubscriptionMetrics:
    validate_period(period_start, period_end)
    with get_connection() as conn:
        active = queries.get_active_subscriptions_count(conn, period_end)
        counts = queries.get_subscription_event_counts(conn, period_start, period_end)

    return SubscriptionMetrics(
        active_subscriptions=active,
        new_subscriptions=counts.get("new", 0),
        upgrades=counts.get("upgrade", 0),
        downgrades=counts.get("downgrade", 0),
        cancellations=counts.get("cancellation", 0),
    )


def get_churn_metrics(period_start: date, period_end: date) -> ChurnMetrics:
    validate_period(period_start, period_end)
    with get_connection() as conn:
        churned_customers = queries.get_churned_customers_count(conn, period_start, period_end)
        customers_at_beginning = queries.get_active_customers_count(conn, period_start)
        churned_mrr = queries.get_mrr_change(conn, period_start, period_end, "cancellation")
        beginning_mrr = queries.get_mrr(conn, period_start)
        expansion_mrr = queries.get_mrr_change(conn, period_start, period_end, "upgrade")
        contraction_mrr = queries.get_mrr_change(conn, period_start, period_end, "downgrade")

    customer_churn_rate = (
        0.0 if customers_at_beginning == 0 else round(churned_customers / customers_at_beginning * 100, 2)
    )
    revenue_churn_rate = 0.0 if beginning_mrr == 0 else round(abs(churned_mrr) / beginning_mrr * 100, 2)
    nrr = (
        0.0
        if beginning_mrr == 0
        else round((beginning_mrr + expansion_mrr + contraction_mrr + churned_mrr) / beginning_mrr * 100, 2)
    )

    return ChurnMetrics(
        churned_customers=churned_customers,
        customer_churn_rate=customer_churn_rate,
        churned_mrr=churned_mrr,
        revenue_churn_rate=revenue_churn_rate,
        nrr=nrr,
    )
