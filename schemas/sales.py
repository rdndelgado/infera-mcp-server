"""Request/response schemas for sales_tools.py (PRD_V2 §10.5)."""

from pydantic import BaseModel


class SalesMetrics(BaseModel):
    closed_revenue: float
    won_deals: int
    lost_deals: int
    win_rate: float
    average_deal_size: float


class SalesPipeline(BaseModel):
    pipeline_value: float
    weighted_pipeline: float
    open_opportunities: int
