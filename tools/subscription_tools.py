"""FastMCP tool definitions: get_subscription_metrics, get_churn_metrics (PRD_V2 §10.4)."""

from datetime import date

from app import mcp
from schemas.subscription import ChurnMetrics, SubscriptionMetrics
from services import subscription_service


@mcp.tool
def get_subscription_metrics(period_start: date, period_end: date) -> SubscriptionMetrics:
    """Active subscriptions plus new/upgrade/downgrade/cancellation counts for a period."""
    return subscription_service.get_subscription_metrics(period_start, period_end)


@mcp.tool
def get_churn_metrics(period_start: date, period_end: date) -> ChurnMetrics:
    """Customer churn rate, revenue churn rate, and NRR for a period."""
    return subscription_service.get_churn_metrics(period_start, period_end)
