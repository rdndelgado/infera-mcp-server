"""Connection client for the analytical warehouse Postgres database.

DATABASE_URL resolves to Supabase if SUPABASE_DB_URL is set, else falls back to
the local docker-compose Postgres (helpers.constants.DATABASE_URL / DB_SOURCE).
"""

import psycopg

from helpers.constants import DATABASE_URL, DB_SOURCE
from utils.logger import get_logger

logger = get_logger(__name__)

_logged_source = False


def get_connection() -> psycopg.Connection:
    global _logged_source
    conn = psycopg.connect(DATABASE_URL)
    if not _logged_source:
        logger.info(f"Warehouse DB connected via {DB_SOURCE}")
        _logged_source = True
    return conn
