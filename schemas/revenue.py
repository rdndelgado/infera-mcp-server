"""Request/response schemas for revenue_tools.py (PRD_V2 §10.2)."""

from datetime import date
from typing import Literal

from pydantic import BaseModel

# Values here must match helpers.constants.SUPPORTED_INTERVALS / SUPPORTED_BREAKDOWN_DIMENSIONS —
# duplicated because typing.Literal needs static values, not a runtime tuple.
RevenueInterval = Literal["day", "month", "quarter"]
RevenueBreakdownDimension = Literal["customer", "plan", "product"]


class RevenueMetrics(BaseModel):
    mrr: float
    arr: float
    new_mrr: float
    expansion_mrr: float
    contraction_mrr: float
    churned_mrr: float
    net_new_mrr: float


class RevenueTrendPoint(BaseModel):
    period_start: date
    mrr: float


class RevenueBreakdownItem(BaseModel):
    label: str
    mrr: float
