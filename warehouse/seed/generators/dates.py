"""dim_date generator. Grain: one row per calendar date."""

from datetime import timedelta

from .config import WAREHOUSE_END, WAREHOUSE_START
from .util import daterange, date_key


def generate_dates() -> list[dict]:
    rows = []
    for d in daterange(WAREHOUSE_START, WAREHOUSE_END):
        next_day = d + timedelta(days=1)
        is_month_end = next_day.month != d.month
        rows.append(
            {
                "date_key": date_key(d),
                "date": d,
                "day": d.day,
                "day_of_week": d.weekday(),
                "day_name": d.strftime("%A"),
                "week": int(d.strftime("%V")),
                "month": d.month,
                "month_name": d.strftime("%B"),
                "quarter": (d.month - 1) // 3 + 1,
                "year": d.year,
                "is_month_start": d.day == 1,
                "is_month_end": is_month_end,
            }
        )
    return rows
