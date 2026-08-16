-- Fact tables for the B2B/SaaS analytical warehouse (PRD_V2 star schema).
-- Requires dimensions.sql to have run first (FK targets).

CREATE TABLE IF NOT EXISTS fact_sales (
    sales_key         BIGSERIAL PRIMARY KEY,
    date_key           INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key       INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key        INTEGER NOT NULL REFERENCES dim_product(product_key),
    plan_key           INTEGER NOT NULL REFERENCES dim_plan(plan_key),

    opportunity_id      VARCHAR(30) NOT NULL,
    deal_amount          NUMERIC(12,2) NOT NULL CHECK (deal_amount >= 0),
    contract_value        NUMERIC(12,2) NOT NULL CHECK (contract_value >= 0),
    currency               VARCHAR(3) NOT NULL DEFAULT 'USD',
    sales_stage             VARCHAR(50) NOT NULL,
    sales_status              VARCHAR(20) NOT NULL CHECK (sales_status IN ('won', 'lost')),
    sales_rep                  VARCHAR(100) NOT NULL,
    closed_at                    TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_subscription_snapshot (
    subscription_snapshot_key   BIGSERIAL PRIMARY KEY,
    snapshot_date_key             INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key                   INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key                     INTEGER NOT NULL REFERENCES dim_product(product_key),
    plan_key                         INTEGER NOT NULL REFERENCES dim_plan(plan_key),

    subscription_id                   VARCHAR(30) NOT NULL,
    subscription_status                 VARCHAR(20) NOT NULL,   -- active, cancelled
    mrr                                   NUMERIC(12,2) NOT NULL CHECK (mrr >= 0),
    arr                                     NUMERIC(12,2) NOT NULL CHECK (arr >= 0),
    quantity                                 INTEGER NOT NULL CHECK (quantity > 0),
    subscription_start_date                   DATE NOT NULL,
    subscription_end_date                       DATE,

    UNIQUE (snapshot_date_key, subscription_id)
);

CREATE TABLE IF NOT EXISTS fact_subscription_events (
    subscription_event_key   BIGSERIAL PRIMARY KEY,
    date_key                   INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key                 INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key                    INTEGER NOT NULL REFERENCES dim_product(product_key),
    plan_key                         INTEGER NOT NULL REFERENCES dim_plan(plan_key),

    subscription_id                    VARCHAR(30) NOT NULL,
    event_type                           VARCHAR(20) NOT NULL CHECK (
        event_type IN ('new', 'upgrade', 'downgrade', 'cancellation', 'reactivation')
    ),
    previous_plan_key                      INTEGER REFERENCES dim_plan(plan_key),
    new_plan_key                             INTEGER REFERENCES dim_plan(plan_key),
    previous_mrr                               NUMERIC(12,2),
    new_mrr                                      NUMERIC(12,2),
    mrr_change                                     NUMERIC(12,2) NOT NULL,
    event_timestamp                                  TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_pipeline_snapshot (
    pipeline_snapshot_key   BIGSERIAL PRIMARY KEY,
    snapshot_date_key         INTEGER NOT NULL REFERENCES dim_date(date_key),
    customer_key                INTEGER NOT NULL REFERENCES dim_customer(customer_key),
    product_key                   INTEGER NOT NULL REFERENCES dim_product(product_key),
    plan_key                        INTEGER NOT NULL REFERENCES dim_plan(plan_key),

    opportunity_id                    VARCHAR(30) NOT NULL,
    pipeline_stage                      VARCHAR(50) NOT NULL,
    pipeline_status                       VARCHAR(20) NOT NULL CHECK (
        pipeline_status IN ('open', 'won', 'lost')
    ),
    amount                                   NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    probability                                NUMERIC(5,2) NOT NULL CHECK (probability BETWEEN 0 AND 100),
    weighted_amount                              NUMERIC(12,2) NOT NULL CHECK (weighted_amount >= 0),
    expected_close_date                            DATE NOT NULL,

    UNIQUE (snapshot_date_key, opportunity_id)
);

-- FK lookup indexes: every fact is queried/joined by these constantly.
CREATE INDEX IF NOT EXISTS idx_fact_sales_date ON fact_sales(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer ON fact_sales(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_plan ON fact_sales(plan_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_status ON fact_sales(sales_status);

CREATE INDEX IF NOT EXISTS idx_fact_sub_snapshot_date ON fact_subscription_snapshot(snapshot_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sub_snapshot_customer ON fact_subscription_snapshot(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sub_snapshot_plan ON fact_subscription_snapshot(plan_key);
CREATE INDEX IF NOT EXISTS idx_fact_sub_snapshot_subscription ON fact_subscription_snapshot(subscription_id);

CREATE INDEX IF NOT EXISTS idx_fact_sub_events_date ON fact_subscription_events(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sub_events_customer ON fact_subscription_events(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_sub_events_subscription ON fact_subscription_events(subscription_id);
CREATE INDEX IF NOT EXISTS idx_fact_sub_events_type ON fact_subscription_events(event_type);

CREATE INDEX IF NOT EXISTS idx_fact_pipeline_snapshot_date ON fact_pipeline_snapshot(snapshot_date_key);
CREATE INDEX IF NOT EXISTS idx_fact_pipeline_snapshot_customer ON fact_pipeline_snapshot(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_pipeline_snapshot_status ON fact_pipeline_snapshot(pipeline_status);
