"""FastMCP tool definitions: get_sales_metrics, get_sales_pipeline (PRD_V2 §10.5)."""

from datetime import date

from app import mcp
from schemas.sales import SalesMetrics, SalesPipeline
from services import sales_service


@mcp.tool
def get_sales_metrics(period_start: date, period_end: date) -> SalesMetrics:
    """Closed revenue, won/lost deal counts, win rate, and average deal size for a period."""
    return sales_service.get_sales_metrics(period_start, period_end)


@mcp.tool
def get_sales_pipeline(as_of_date: date) -> SalesPipeline:
    """Open pipeline value, weighted pipeline, and open opportunity count as of a date."""
    return sales_service.get_sales_pipeline(as_of_date)
