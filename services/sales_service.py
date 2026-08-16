"""Business logic for get_sales_metrics / get_sales_pipeline (PRD_V2 §10.5).
Win rate / avg deal size / pipeline value / weighted pipeline formulas per §9.
"""

from datetime import date

from db.warehouse import queries
from db.warehouse.client import get_connection
from schemas.sales import SalesMetrics, SalesPipeline
from utils.validators import validate_period


def get_sales_metrics(period_start: date, period_end: date) -> SalesMetrics:
    validate_period(period_start, period_end)
    with get_connection() as conn:
        agg = queries.get_sales_aggregates(conn, period_start, period_end)

    won = agg.get("won", {"count": 0, "revenue": 0.0})
    lost = agg.get("lost", {"count": 0, "revenue": 0.0})
    won_deals, lost_deals = won["count"], lost["count"]
    closed_revenue = won["revenue"]

    win_rate = 0.0 if (won_deals + lost_deals) == 0 else round(won_deals / (won_deals + lost_deals) * 100, 2)
    average_deal_size = 0.0 if won_deals == 0 else round(closed_revenue / won_deals, 2)

    return SalesMetrics(
        closed_revenue=closed_revenue,
        won_deals=won_deals,
        lost_deals=lost_deals,
        win_rate=win_rate,
        average_deal_size=average_deal_size,
    )


def get_sales_pipeline(as_of_date: date) -> SalesPipeline:
    with get_connection() as conn:
        agg = queries.get_pipeline_aggregates(conn, as_of_date)

    return SalesPipeline(
        pipeline_value=float(agg["pipeline_value"]),
        weighted_pipeline=float(agg["weighted_pipeline"]),
        open_opportunities=agg["open_opportunities"],
    )
