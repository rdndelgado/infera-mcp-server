"""Connection client for the analytical warehouse Postgres database.

Points at the local docker-compose Postgres for now (helpers.constants.DATABASE_URL).
Swap for a Supabase Postgres connection string when a real project is provisioned —
callers of get_connection() do not need to change.
"""

import psycopg

from helpers.constants import DATABASE_URL


def get_connection() -> psycopg.Connection:
    return psycopg.connect(DATABASE_URL)
