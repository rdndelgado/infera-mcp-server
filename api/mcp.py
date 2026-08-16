"""Vercel serverless entrypoint — deployed URL will be <project>.vercel.app/api/mcp.

Vercel's Python runtime serves a WSGI/ASGI `app` variable directly; it owns
the process, so app.py's `mcp.run()` is never called here. stateless_http=True
because each invocation may hit a different, short-lived function instance —
there's no persistent session to hold state across requests.

NOT YET VERIFIED against a live Vercel deployment (no account access here) —
test with `vercel dev` before pushing. path="/" so the ASGI app answers at
its own root, matching whatever Vercel already routed to /api/mcp; setting a
non-root path here would double up the URL.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import mcp  # noqa: E402  (needs sys.path fix above first)

app = mcp.http_app(path="/", stateless_http=True)
