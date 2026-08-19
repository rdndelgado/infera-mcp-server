"""Centralized environment extraction and application constants (PRD_V2 §12)."""

from decouple import config

# --- Supabase ---
SUPABASE_URL = config("SUPABASE_URL", default="")
SUPABASE_KEY = config("SUPABASE_KEY", default="")
# Direct Postgres connection string from Supabase (Project Settings > Database
# > Connection string). Different from SUPABASE_URL/KEY above, which are for
# the Supabase SDK/REST API, not used by db/warehouse/client.py.
SUPABASE_DB_URL = config("SUPABASE_DB_URL", default="")

# --- MCP ---
MCP_API_KEY = config("MCP_API_KEY", default="")
# This server's own public URL — required by SupabaseProvider (OAuth resource/
# redirect metadata). Update to the real Vercel URL once deployed.
MCP_BASE_URL = config("MCP_BASE_URL", default="http://localhost:8321")

# --- Application ---
LOG_LEVEL = config("LOG_LEVEL", default="INFO")
ENVIRONMENT = config("ENVIRONMENT", default="development")

# --- Local warehouse Postgres (docker-compose) ---
# Offline dev fallback only. If SUPABASE_DB_URL is set, DATABASE_URL below
# uses it instead — Supabase is the real target now.
POSTGRES_USER = config("POSTGRES_USER", default="postgres")
POSTGRES_PASSWORD = config("POSTGRES_PASSWORD", default="postgres")
POSTGRES_DB = config("POSTGRES_DB", default="saas_db")
POSTGRES_HOST = config("POSTGRES_HOST", default="localhost")
POSTGRES_PORT = config("POSTGRES_PORT", default="5432")

DATABASE_URL = SUPABASE_DB_URL or (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

# Which backend DATABASE_URL actually resolved to — used only for logging,
# never exposed in tool output.
DB_SOURCE = "supabase" if SUPABASE_DB_URL else "local postgres"

# --- Non-secret application constants ---
DEFAULT_TOP_CUSTOMERS = 10
MAX_TOP_CUSTOMERS = 50
SUPPORTED_INTERVALS = ("day", "month", "quarter")
SUPPORTED_BREAKDOWN_DIMENSIONS = ("customer", "plan", "product")
