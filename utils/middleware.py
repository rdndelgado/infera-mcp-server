"""MCP call observability — logs every tool call (client identity, tool,
timing, success/failure) to stdout and the mcp_clients/mcp_calls tables.

A logging/persistence failure must never break the actual tool call — the DB
write is best-effort and swallows its own errors.
"""

import asyncio
import time

from fastmcp.server.dependencies import get_access_token
from fastmcp.server.middleware import Middleware, MiddlewareContext

from db.warehouse import queries
from db.warehouse.client import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def _persist(client_id, auth_type, client_name, email, tool_name, arguments, duration_ms, success, error_message):
    with get_connection() as conn:
        queries.upsert_mcp_client(conn, client_id, auth_type, client_name, email)
        queries.log_mcp_call(conn, client_id, tool_name, arguments, duration_ms, success, error_message)


class ObservabilityMiddleware(Middleware):
    async def on_call_tool(self, context: MiddlewareContext, call_next):
        access_token = get_access_token()
        if access_token:
            client_id = access_token.client_id
            claims = access_token.claims or {}
            auth_type = claims.get("auth_type", "oauth")
            email = claims.get("email")
            client_name = claims.get("client_name") or email or client_id
        else:
            client_id = "unauthenticated"
            auth_type = "unauthenticated"
            email = None
            client_name = "unauthenticated"
        tool_name = context.message.name
        arguments = context.message.arguments

        start = time.monotonic()
        success = True
        error_message = None
        try:
            result = await call_next(context)
            success = not result.is_error
            return result
        except Exception as exc:
            success = False
            error_message = str(exc)[:500]
            raise
        finally:
            duration_ms = int((time.monotonic() - start) * 1000)
            logger.info(f"tool={tool_name} client={client_id} success={success} duration_ms={duration_ms}")
            try:
                await asyncio.to_thread(
                    _persist,
                    client_id,
                    auth_type,
                    client_name,
                    email,
                    tool_name,
                    arguments,
                    duration_ms,
                    success,
                    error_message,
                )
            except Exception:
                logger.error(f"Failed to persist mcp_calls for tool={tool_name}", exc_info=True)
