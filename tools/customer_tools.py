"""FastMCP tool definitions: get_customer_metrics, get_top_customers (PRD_V2 §10.3)."""

from datetime import date
from typing import Annotated

from pydantic import Field

from app import mcp
from helpers.constants import DEFAULT_TOP_CUSTOMERS, MAX_TOP_CUSTOMERS
from schemas.customer import CustomerMetrics, TopCustomer
from services import customer_service


@mcp.tool
def get_customer_metrics(period_start: date, period_end: date) -> CustomerMetrics:
    """Active/new/churned customer counts and growth rate for a period."""
    return customer_service.get_customer_metrics(period_start, period_end)


@mcp.tool
def get_top_customers(
    as_of_date: date,
    limit: Annotated[int, Field(ge=1, le=MAX_TOP_CUSTOMERS)] = DEFAULT_TOP_CUSTOMERS,
) -> list[TopCustomer]:
    """Highest-MRR customers as of a given date."""
    return customer_service.get_top_customers(as_of_date, limit)
