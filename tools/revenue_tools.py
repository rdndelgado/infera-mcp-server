"""FastMCP tool definitions: get_revenue_metrics, get_revenue_trend,
get_revenue_breakdown (PRD_V2 §10.2).
"""

from datetime import date

from app import mcp
from schemas.revenue import (
    RevenueBreakdownDimension,
    RevenueBreakdownItem,
    RevenueInterval,
    RevenueMetrics,
    RevenueTrendPoint,
)
from services import revenue_service


@mcp.tool
def get_revenue_metrics(period_start: date, period_end: date) -> RevenueMetrics:
    """MRR, ARR, and new/expansion/contraction/churned/net-new MRR for a period."""
    return revenue_service.get_revenue_metrics(period_start, period_end)


@mcp.tool
def get_revenue_trend(start_date: date, end_date: date, interval: RevenueInterval) -> list[RevenueTrendPoint]:
    """MRR over time, bucketed by day, month, or quarter."""
    return revenue_service.get_revenue_trend(start_date, end_date, interval)


@mcp.tool
def get_revenue_breakdown(
    period_start: date, period_end: date, dimension: RevenueBreakdownDimension
) -> list[RevenueBreakdownItem]:
    """MRR as of period_end, broken down by customer, plan, or product."""
    return revenue_service.get_revenue_breakdown(period_start, period_end, dimension)
