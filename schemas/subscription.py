"""Request/response schemas for subscription_tools.py (PRD_V2 §10.4)."""

from pydantic import BaseModel


class SubscriptionMetrics(BaseModel):
    active_subscriptions: int
    new_subscriptions: int
    upgrades: int
    downgrades: int
    cancellations: int


class ChurnMetrics(BaseModel):
    churned_customers: int
    customer_churn_rate: float
    churned_mrr: float
    revenue_churn_rate: float
    nrr: float
