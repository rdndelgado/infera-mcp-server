"""Fixed generation parameters. Change these to resize/reshape the dataset —
everything else derives from them, and generation stays deterministic
(seed=42) across reruns as long as these don't change.
"""

from datetime import date

WAREHOUSE_START = date(2023, 1, 1)
WAREHOUSE_END = date(2024, 12, 31)

# Intentional anomaly window (PRD_V2 doesn't specify patterns the way V1 did;
# this mirrors that intent for discoverability): elevated churn + depressed
# sales win rate concentrated in this month, so "why did revenue decline in
# March 2024" has a real, findable answer in the data.
ANOMALY_MONTH_START = date(2024, 3, 1)
ANOMALY_MONTH_END = date(2024, 3, 31)
ANOMALY_PRODUCT_ID = "PROD-02"  # the product whose churn spikes
ANOMALY_PLAN_TIER = "Growth"  # the tier within that product that spikes
ANOMALY_FORCE_CHURN_PROB = 0.55  # among eligible subs, odds we force a March cancellation
ANOMALY_LOST_CONCENTRATION = 0.25  # fraction of all lost deals forced to close in the anomaly month

NUM_CUSTOMERS_WON = 300  # companies that became paying subscribers
NUM_CUSTOMERS_PROSPECT = 150  # companies that only ever had a lost deal

COMPANY_SIZE_BUCKETS = ["1-10", "11-50", "51-200", "201-1000", "1000+"]
COMPANY_SIZE_WEIGHTS = [0.35, 0.30, 0.20, 0.10, 0.05]

INDUSTRIES = [
    "SaaS", "FinTech", "Healthcare", "Retail", "Manufacturing",
    "Education", "Media", "Logistics", "Real Estate", "Legal Services",
]

COUNTRIES = ["United States", "United Kingdom", "Germany", "Canada", "Australia", "France", "Netherlands"]
COUNTRY_WEIGHTS = [0.45, 0.15, 0.10, 0.10, 0.08, 0.07, 0.05]

SALES_REPS = [
    "Jordan Blake", "Priya Nair", "Marcus Chen", "Sofia Ramirez",
    "Ethan Wright", "Aisha Bello", "Liam O'Connor", "Nina Petrov",
]

SEATS_BY_COMPANY_SIZE = {
    "1-10": (1, 3),
    "11-50": (3, 10),
    "51-200": (10, 40),
    "201-1000": (30, 150),
    "1000+": (100, 500),
}
