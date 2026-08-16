"""Cross-cutting parameter validation shared by tools/services (PRD_V2 §13).

Deferred beyond this: full per-tool parameter validation lands with each
tool in tools/*.py.
"""

from datetime import date


def validate_period(period_start: date, period_end: date) -> None:
    if period_start > period_end:
        raise ValueError(
            f"period_start ({period_start}) must not be after period_end ({period_end})"
        )
