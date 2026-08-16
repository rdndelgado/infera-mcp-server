-- Dimension tables for the B2B/SaaS analytical warehouse (PRD_V2 star schema).
-- Load order: dim_date, dim_customer, dim_product have no FK dependencies;
-- dim_plan depends on dim_product.

CREATE TABLE IF NOT EXISTS dim_date (
    date_key         INTEGER PRIMARY KEY,        -- YYYYMMDD
    date              DATE NOT NULL UNIQUE,
    day               SMALLINT NOT NULL,
    day_of_week       SMALLINT NOT NULL,          -- 0=Monday .. 6=Sunday
    day_name          VARCHAR(10) NOT NULL,
    week              SMALLINT NOT NULL,
    month             SMALLINT NOT NULL,
    month_name        VARCHAR(10) NOT NULL,
    quarter           SMALLINT NOT NULL,
    year              SMALLINT NOT NULL,
    is_month_start    BOOLEAN NOT NULL,
    is_month_end      BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_customer (
    customer_key       SERIAL PRIMARY KEY,
    customer_id        VARCHAR(20) NOT NULL UNIQUE,   -- business/source id
    customer_name       VARCHAR(200) NOT NULL,
    industry            VARCHAR(100) NOT NULL,
    company_size        VARCHAR(50) NOT NULL,          -- e.g. 1-10, 11-50, 51-200, 201-1000, 1000+
    country              VARCHAR(100) NOT NULL,
    customer_segment    VARCHAR(50) NOT NULL,          -- e.g. SMB, Mid-Market, Enterprise
    acquisition_date    DATE NOT NULL,
    status                VARCHAR(20) NOT NULL           -- active, churned
);

CREATE TABLE IF NOT EXISTS dim_product (
    product_key        SERIAL PRIMARY KEY,
    product_id          VARCHAR(20) NOT NULL UNIQUE,
    product_name         VARCHAR(200) NOT NULL,
    product_category      VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_plan (
    plan_key             SERIAL PRIMARY KEY,
    plan_id               VARCHAR(20) NOT NULL UNIQUE,
    plan_name              VARCHAR(200) NOT NULL,
    product_key             INTEGER NOT NULL REFERENCES dim_product(product_key),
    billing_interval        VARCHAR(20) NOT NULL,       -- monthly, annual
    list_price               NUMERIC(10,2) NOT NULL CHECK (list_price >= 0),
    currency                  VARCHAR(3) NOT NULL DEFAULT 'USD'
);

CREATE INDEX IF NOT EXISTS idx_dim_date_year_month ON dim_date(year, month);
CREATE INDEX IF NOT EXISTS idx_dim_customer_segment ON dim_customer(customer_segment);
CREATE INDEX IF NOT EXISTS idx_dim_customer_status ON dim_customer(status);
CREATE INDEX IF NOT EXISTS idx_dim_plan_product ON dim_plan(product_key);
