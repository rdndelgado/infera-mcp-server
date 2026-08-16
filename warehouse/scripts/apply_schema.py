"""Applies warehouse/schema/*.sql against whatever DATABASE_URL resolves to
(Supabase if SUPABASE_DB_URL is set, else local docker Postgres).

Needed because Supabase doesn't auto-run init SQL the way the local
docker-compose Postgres does (docker-entrypoint-initdb.d). Safe to rerun —
every statement is CREATE TABLE/INDEX IF NOT EXISTS.

Run as: python -m warehouse.scripts.apply_schema
"""

from pathlib import Path

from db.warehouse.client import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "schema"
SCHEMA_FILES = ["dimensions.sql", "facts.sql"]  # order matters: facts FK-reference dimensions


def main() -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            for filename in SCHEMA_FILES:
                sql = (SCHEMA_DIR / filename).read_text()
                logger.info(f"Applying {filename}...")
                cur.execute(sql)
        conn.commit()
    logger.info("Schema applied.")


if __name__ == "__main__":
    main()
