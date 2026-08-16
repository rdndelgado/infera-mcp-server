"""Request/response schemas for business_tools.py (PRD_V2 §10.1)."""

from pydantic import BaseModel

from schemas.customer import CustomerMetrics
from schemas.revenue import RevenueMetrics
from schemas.sales import SalesMetrics
from schemas.subscription import ChurnMetrics


class BusinessSummary(BaseModel):
    revenue: RevenueMetrics
    customers: CustomerMetrics
    churn: ChurnMetrics
    sales: SalesMetrics


class PeriodComparison(BaseModel):
    current: BusinessSummary
    previous: BusinessSummary
    mrr_change_pct: float
    active_customers_change_pct: float
    closed_revenue_change_pct: float
