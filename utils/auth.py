"""Auth for the deployed MCP endpoint (PRD_V2 §6, §14).

Two schemes accepted on the same running server, distinguished per-request by
token shape (JWTs are always three dot-separated segments; our own static
keys, generated with secrets.token_urlsafe, never contain a dot):

- Supabase OAuth JWTs — verified against Supabase's JWKS, giving each remote
  client a real identity (`sub`/email claims) instead of one shared secret.
- Static per-client keys — looked up in mcp_clients by SHA-256 hash (never
  the raw key — hashing is one-way; verification re-hashes the incoming
  token and compares, same as password auth). Provisioned via
  warehouse/scripts/seed_mcp_client_local.py (gitignored, not committed).

Only enforced by the HTTP transport (api/mcp.py) — stdio (app.py's
mcp.run(), local Claude Desktop/Code) has no HTTP layer to apply it to, so
this is safe to wire in globally.
"""

import asyncio
import hashlib

from fastmcp.server.auth import AuthProvider
from fastmcp.server.auth.auth import AccessToken, TokenVerifier
from fastmcp.server.auth.providers.jwt import JWTVerifier
from fastmcp.server.auth.providers.supabase import SupabaseProvider

from db.warehouse import queries
from db.warehouse.client import get_connection
from helpers.constants import MCP_API_KEY, MCP_BASE_URL, SUPABASE_URL
from utils.logger import get_logger

logger = get_logger(__name__)


class DBBackedStaticVerifier(TokenVerifier):
    """Looks up a static key's SHA-256 hash in mcp_clients. No raw keys ever
    stored or compared — see module docstring."""

    async def verify_token(self, token: str) -> AccessToken | None:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        row = await asyncio.to_thread(self._lookup, token_hash)
        if row is None:
            return None
        client_id, client_name = row
        return AccessToken(
            token=token,
            client_id=client_id,
            scopes=[],
            claims={"auth_type": "static", "client_name": client_name},
        )

    def _lookup(self, token_hash: str) -> tuple | None:
        with get_connection() as conn:
            return queries.get_mcp_client_by_access_token(conn, token_hash)


class CompositeVerifier(TokenVerifier):
    """Routes to JWT or static-key verification based on token shape — a JWT
    is always header.payload.signature (two dots); our static keys never
    contain one."""

    def __init__(self, jwt_verifier: TokenVerifier, static_verifier: TokenVerifier):
        super().__init__()
        self._jwt = jwt_verifier
        self._static = static_verifier

    async def verify_token(self, token: str) -> AccessToken | None:
        if token.count(".") == 2:
            return await self._jwt.verify_token(token)
        return await self._static.verify_token(token)


def get_auth_provider() -> AuthProvider | None:
    if SUPABASE_URL:
        jwt_verifier = JWTVerifier(
            jwks_uri=f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json",
            issuer=f"{SUPABASE_URL}/auth/v1",
            algorithm="ES256",
            audience="authenticated",
        )
        logger.info("Auth: Supabase OAuth + static keys")
        return SupabaseProvider(
            project_url=SUPABASE_URL,
            base_url=MCP_BASE_URL,
            algorithm="ES256",
            token_verifier=CompositeVerifier(jwt_verifier, DBBackedStaticVerifier()),
        )
    if MCP_API_KEY:
        logger.info("Auth: static keys only (SUPABASE_URL not set)")
        return DBBackedStaticVerifier()
    logger.warning("No auth configured — server running WITHOUT auth.")
    return None
