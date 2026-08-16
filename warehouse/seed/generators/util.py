"""Shared helpers for the seed generators. random.seed(42) makes the whole
pipeline reproducible; call seed_all() once before generating anything.
"""

import random
from datetime import date, timedelta

from faker import Faker

SEED = 42

fake = Faker()


def seed_all() -> None:
    random.seed(SEED)
    Faker.seed(SEED)


def daterange(start: date, end: date):
    """Yield every date from start to end, inclusive."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def date_key(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def round_money(value: float) -> float:
    return round(value, 2)


def weighted_choice(options: list, weights: list):
    return random.choices(options, weights=weights, k=1)[0]
