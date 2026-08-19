"""Provisions a new static MCP client: generates a random key, stores only
its SHA-256 hash in mcp_clients.access_token, and prints the raw key once.
That print is the only time the raw key exists outside the requester's
hands — deliver it to them out-of-band immediately. Lost key means rotate
(rerun with --rotate), not recover — hashing is one-way, see utils/auth.py.

Run as: python -m warehouse.scripts.provision_mcp_client --name "Acme Corp"
Rotate: python -m warehouse.scripts.provision_mcp_client --name "Acme Corp" --rotate
"""

import argparse
import re
import secrets
from hashlib import sha256

from db.warehouse.client import get_connection
from utils.logger import get_logger

logger = get_logger(__name__)


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return f"static-{slug}"


def provision(client_id: str, client_name: str) -> str:
    raw_key = secrets.token_urlsafe(32)
    token_hash = sha256(raw_key.encode()).hexdigest()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO mcp_clients (client_id, auth_type, client_name, access_token, is_active) "
                "VALUES (%s, 'static', %s, %s, true) "
                "ON CONFLICT (client_id) DO UPDATE SET "
                "access_token = EXCLUDED.access_token, client_name = EXCLUDED.client_name, is_active = true",
                (client_id, client_name, token_hash),
            )
    return raw_key


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Human-readable client name, e.g. 'Acme Corp'")
    parser.add_argument(
        "--rotate", action="store_true", help="Replace an existing client's key instead of erroring on conflict"
    )
    args = parser.parse_args()

    client_id = _slugify(args.name)
    raw_key = provision(client_id, args.name)

    action = "Rotated" if args.rotate else "Provisioned"
    print(f"\n{action} static client '{args.name}' (client_id={client_id})")
    print(f"Raw key — save this now, it will not be shown again:\n\n{raw_key}\n")
