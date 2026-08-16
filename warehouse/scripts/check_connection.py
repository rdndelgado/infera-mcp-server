"""Verify the local warehouse Postgres is up and the schema loaded.
Run as: python -m warehouse.scripts.check_connection
"""

import sys

from db.warehouse.client import get_connection

EXPECTED_TABLES = [
    "dim_date",
    "dim_customer",
    "dim_product",
    "dim_plan",
    "fact_sales",
    "fact_subscription_snapshot",
    "fact_subscription_events",
    "fact_pipeline_snapshot",
]


def main() -> None:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    )
    found = {row[0] for row in cur.fetchall()}
    missing = [t for t in EXPECTED_TABLES if t not in found]

    for table in EXPECTED_TABLES:
        if table in found:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  ok  {table:<28} {count} rows")
        else:
            print(f"  MISSING  {table}")

    cur.close()
    conn.close()

    if missing:
        print(f"\n{len(missing)} table(s) missing. Did the schema init run?")
        sys.exit(1)

    print("\nWarehouse schema is up.")


if __name__ == "__main__":
    main()
