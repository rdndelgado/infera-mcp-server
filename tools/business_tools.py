"""FastMCP tool definitions: get_business_summary, compare_periods (PRD_V2 §10.1)."""

from datetime import date

from app import mcp
from schemas.business import BusinessSummary, PeriodComparison
from services import business_service


@mcp.tool
def get_business_summary(period_start: date, period_end: date) -> BusinessSummary:
    """High-level business health snapshot: revenue, customers, churn, sales."""
    return business_service.get_business_summary(period_start, period_end)


@mcp.tool
def compare_periods(
    current_start: date, current_end: date, previous_start: date, previous_end: date
) -> PeriodComparison:
    """Compare business performance across two periods."""
    return business_service.compare_periods(current_start, current_end, previous_start, previous_end)
