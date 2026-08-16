"""Supabase SDK client, for non-warehouse Supabase-specific needs (e.g. auth).

Deferred until a real Supabase project is provisioned — see helpers.constants
.SUPABASE_URL / SUPABASE_KEY. The warehouse itself is accessed directly via
db/warehouse/client.py (a plain Postgres connection), not through this client.
"""
