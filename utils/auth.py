"""Static bearer-token auth for the deployed MCP endpoint (PRD_V2 §6, §14).

Remote clients must send `Authorization: Bearer <MCP_API_KEY>`. This is a
resource-server-only TokenVerifier (no OAuth flows) — the simplest thing
that satisfies "no unauthenticated MCP access" for the MVP. Swap for a real
OAuth provider later without touching callers of get_auth_provider().
"""

from fastmcp.server.auth.auth import AccessToken, TokenVerifier

from helpers.constants import ENVIRONMENT, MCP_API_KEY
from utils.logger import get_logger

logger = get_logger(__name__)


class StaticBearerTokenVerifier(TokenVerifier):
    def __init__(self, expected_token: str):
        super().__init__()
        self._expected_token = expected_token

    async def verify_token(self, token: str) -> AccessToken | None:
        if token != self._expected_token:
            return None
        return AccessToken(token=token, client_id="static", scopes=[])


def get_auth_provider() -> StaticBearerTokenVerifier | None:
    if MCP_API_KEY:
        return StaticBearerTokenVerifier(MCP_API_KEY)
    if ENVIRONMENT == "production":
        raise RuntimeError("MCP_API_KEY is required when ENVIRONMENT=production")
    logger.warning("MCP_API_KEY not set — server running WITHOUT auth (dev only).")
    return None
