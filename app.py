"""FastMCP server entrypoint (PRD_V2 §5).

Tool modules (tools/*.py) import `mcp` from this module and register
themselves via @mcp.tool at import time — hence the import block below runs
*after* `mcp` is defined, not at the top of the file.

`python app.py` runs stdio transport, for local MCP clients (Claude Desktop/
Code) that spawn this as a subprocess. For remote/Vercel HTTP access, see
api/index.py, which mounts mcp.http_app() instead — Vercel manages the
server process itself, so this file's `mcp.run()` is never invoked there.
"""

from fastmcp import FastMCP

from db.warehouse.client import get_connection
from helpers.constants import DB_SOURCE
from utils.auth import get_auth_provider
from utils.logger import get_logger
from utils.middleware import ObservabilityMiddleware

logger = get_logger(__name__)

mcp = FastMCP("Infera MCP Server", auth=get_auth_provider())
mcp.add_middleware(ObservabilityMiddleware())


def _verify_db_connection() -> None:
    label = "Supabase" if DB_SOURCE == "supabase" else "Postgres (local)"
    conn = get_connection()
    try:
        conn.execute("SELECT 1")
    finally:
        conn.close()
    logger.info(f"Connected to DB: {label}")


_verify_db_connection()

from tools import (  # noqa: E402  (must follow `mcp` definition above)
    business_tools,
    customer_tools,
    revenue_tools,
    sales_tools,
    subscription_tools,
)

if __name__ == "__main__":
    mcp.run()
