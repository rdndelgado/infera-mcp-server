"""Business logic for get_business_summary / compare_periods (PRD_V2 §10.1)."""

from datetime import date

from schemas.business import BusinessSummary, PeriodComparison
from services import customer_service, revenue_service, sales_service, subscription_service
from utils.validators import validate_period


def get_business_summary(period_start: date, period_end: date) -> BusinessSummary:
    validate_period(period_start, period_end)
    return BusinessSummary(
        revenue=revenue_service.get_revenue_metrics(period_start, period_end),
        customers=customer_service.get_customer_metrics(period_start, period_end),
        churn=subscription_service.get_churn_metrics(period_start, period_end),
        sales=sales_service.get_sales_metrics(period_start, period_end),
    )


def _pct_change(current: float, previous: float) -> float:
    return 0.0 if previous == 0 else round((current - previous) / previous * 100, 2)


def compare_periods(
    current_start: date, current_end: date, previous_start: date, previous_end: date
) -> PeriodComparison:
    validate_period(current_start, current_end)
    validate_period(previous_start, previous_end)

    current = get_business_summary(current_start, current_end)
    previous = get_business_summary(previous_start, previous_end)

    return PeriodComparison(
        current=current,
        previous=previous,
        mrr_change_pct=_pct_change(current.revenue.mrr, previous.revenue.mrr),
        active_customers_change_pct=_pct_change(
            current.customers.active_customers, previous.customers.active_customers
        ),
        closed_revenue_change_pct=_pct_change(current.sales.closed_revenue, previous.sales.closed_revenue),
    )
