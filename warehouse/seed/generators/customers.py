"""dim_customer generator.

Produces two populations sharing one table:
  - "won" customers: became paying subscribers (subscriptions.py builds on these)
  - "prospect" customers: only ever had a lost deal, never subscribed

Acquisition dates skew later in the window (more company growth over time),
modeled with a simple quadratic bias.
"""

import random
from datetime import timedelta

from .config import (
    COMPANY_SIZE_BUCKETS,
    COMPANY_SIZE_WEIGHTS,
    COUNTRIES,
    COUNTRY_WEIGHTS,
    INDUSTRIES,
    NUM_CUSTOMERS_PROSPECT,
    NUM_CUSTOMERS_WON,
    WAREHOUSE_END,
    WAREHOUSE_START,
)
from .util import fake, weighted_choice

SEGMENT_BY_SIZE = {
    "1-10": "SMB",
    "11-50": "SMB",
    "51-200": "Mid-Market",
    "201-1000": "Mid-Market",
    "1000+": "Enterprise",
}


def _biased_acquisition_date():
    span_days = (WAREHOUSE_END - WAREHOUSE_START).days
    # sqrt bias skews the distribution toward later dates (more signups over time)
    offset = int((random.random() ** 0.5) * span_days)
    return WAREHOUSE_START + timedelta(days=offset)


def _generate_batch(count: int, id_prefix: str, is_prospect: bool) -> list[dict]:
    rows = []
    for i in range(1, count + 1):
        company_size = weighted_choice(COMPANY_SIZE_BUCKETS, COMPANY_SIZE_WEIGHTS)
        rows.append(
            {
                "customer_id": f"{id_prefix}-{i:05d}",
                "customer_name": fake.company(),
                "industry": random.choice(INDUSTRIES),
                "company_size": company_size,
                "country": weighted_choice(COUNTRIES, COUNTRY_WEIGHTS),
                "customer_segment": SEGMENT_BY_SIZE[company_size],
                "acquisition_date": _biased_acquisition_date(),
                "status": "prospect" if is_prospect else "active",  # "active" resolved later by subscriptions.py
                "is_prospect": is_prospect,
            }
        )
    return rows


def generate_customers() -> list[dict]:
    won = _generate_batch(NUM_CUSTOMERS_WON, "CUST", is_prospect=False)
    prospects = _generate_batch(NUM_CUSTOMERS_PROSPECT, "PROSPECT", is_prospect=True)
    return won + prospects
