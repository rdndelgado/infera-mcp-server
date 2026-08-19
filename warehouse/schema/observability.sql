-- Operational audit log for MCP tool calls — not part of the business star
-- schema (dimensions.sql/facts.sql), kept separate since it's a system/ops
-- concern, not analytical data about the SaaS business itself.

DROP TABLE IF EXISTS mcp_call_log;

CREATE TABLE IF NOT EXISTS mcp_clients (
    client_key      SERIAL PRIMARY KEY,
    client_id       VARCHAR(255) NOT NULL UNIQUE,   -- Supabase sub (oauth) or generated id (static)
    auth_type       VARCHAR(20) NOT NULL CHECK (auth_type IN ('oauth', 'static', 'unauthenticated')),
    client_name     VARCHAR(255),
    email           VARCHAR(255),                    -- oauth only
    access_token    VARCHAR(255) UNIQUE,              -- static only — SHA-256 hash, never raw
    is_active       BOOLEAN NOT NULL DEFAULT true,
    first_seen_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS mcp_calls (
    call_key       BIGSERIAL PRIMARY KEY,
    client_id      VARCHAR(255) NOT NULL REFERENCES mcp_clients(client_id),
    date_created   TIMESTAMPTZ NOT NULL DEFAULT now(),
    tool_name      VARCHAR(100) NOT NULL,
    arguments      JSONB,
    duration_ms    INTEGER NOT NULL CHECK (duration_ms >= 0),
    success        BOOLEAN NOT NULL,
    error_message  TEXT
);

CREATE INDEX IF NOT EXISTS idx_mcp_clients_auth_type  ON mcp_clients(auth_type);
CREATE INDEX IF NOT EXISTS idx_mcp_calls_client_id    ON mcp_calls(client_id);
CREATE INDEX IF NOT EXISTS idx_mcp_calls_tool_name    ON mcp_calls(tool_name);
CREATE INDEX IF NOT EXISTS idx_mcp_calls_date_created ON mcp_calls(date_created);
