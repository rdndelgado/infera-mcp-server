"""Business logic for get_revenue_metrics / get_revenue_trend / get_revenue_breakdown
(PRD_V2 §10.2). MRR/ARR/new/expansion/contraction/churned MRR formulas per §9.
"""

from datetime import date

from db.warehouse import queries
from db.warehouse.client import get_connection
from schemas.revenue import RevenueBreakdownItem, RevenueMetrics, RevenueTrendPoint
from utils.validators import validate_period


def get_revenue_metrics(period_start: date, period_end: date) -> RevenueMetrics:
    validate_period(period_start, period_end)
    with get_connection() as conn:
        mrr = queries.get_mrr(conn, period_end)
        new_mrr = queries.get_mrr_change(conn, period_start, period_end, "new")
        expansion_mrr = queries.get_mrr_change(conn, period_start, period_end, "upgrade")
        contraction_mrr = queries.get_mrr_change(conn, period_start, period_end, "downgrade")
        churned_mrr = queries.get_mrr_change(conn, period_start, period_end, "cancellation")

    return RevenueMetrics(
        mrr=mrr,
        arr=mrr * 12,
        new_mrr=new_mrr,
        expansion_mrr=expansion_mrr,
        contraction_mrr=contraction_mrr,
        churned_mrr=churned_mrr,
        net_new_mrr=new_mrr + expansion_mrr + contraction_mrr + churned_mrr,
    )


def get_revenue_trend(start_date: date, end_date: date, interval: str) -> list[RevenueTrendPoint]:
    validate_period(start_date, end_date)
    with get_connection() as conn:
        rows = queries.get_revenue_trend(conn, start_date, end_date, interval)
    return [RevenueTrendPoint(period_start=r["period_start"], mrr=float(r["mrr"])) for r in rows]


def get_revenue_breakdown(period_start: date, period_end: date, dimension: str) -> list[RevenueBreakdownItem]:
    validate_period(period_start, period_end)
    with get_connection() as conn:
        rows = queries.get_revenue_breakdown(conn, period_end, dimension)
    return [RevenueBreakdownItem(label=r["label"], mrr=float(r["mrr"])) for r in rows]
