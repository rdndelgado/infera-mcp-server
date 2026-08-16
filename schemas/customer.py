"""Request/response schemas for customer_tools.py (PRD_V2 §10.3)."""

from pydantic import BaseModel


class CustomerMetrics(BaseModel):
    active_customers: int
    new_customers: int
    churned_customers: int
    customer_growth_rate: float


class TopCustomer(BaseModel):
    customer_id: str
    customer_name: str
    mrr: float
