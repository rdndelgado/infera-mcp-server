"""Reusable parameterized warehouse queries, called by services/.

No arbitrary SQL: every query here is predefined and takes only bound
parameters. `dimension` in get_revenue_breakdown is mapped through a
whitelist dict, never interpolated directly from caller input.
"""

from datetime import date

from psycopg.rows import dict_row

_DIMENSION_MAP = {
    "customer": ("dim_customer", "customer_key", "customer_name"),
    "plan": ("dim_plan", "plan_key", "plan_name"),
    "product": ("dim_product", "product_key", "product_name"),
}


def _date_key(d: date) -> int:
    return int(d.strftime("%Y%m%d"))


def get_mrr(conn, as_of_date: date) -> float:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(mrr), 0) FROM fact_subscription_snapshot "
            "WHERE snapshot_date_key = %s AND subscription_status = 'active'",
            (_date_key(as_of_date),),
        )
        return float(cur.fetchone()[0])


def get_mrr_change(conn, period_start: date, period_end: date, event_type: str) -> float:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COALESCE(SUM(e.mrr_change), 0) FROM fact_subscription_events e "
            "JOIN dim_date d ON d.date_key = e.date_key "
            "WHERE d.date BETWEEN %s AND %s AND e.event_type = %s",
            (period_start, period_end, event_type),
        )
        return float(cur.fetchone()[0])


def get_active_customers_count(conn, as_of_date: date) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(DISTINCT customer_key) FROM fact_subscription_snapshot "
            "WHERE snapshot_date_key = %s AND subscription_status = 'active'",
            (_date_key(as_of_date),),
        )
        return int(cur.fetchone()[0])


def get_new_customers_count(conn, period_start: date, period_end: date) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(DISTINCT e.customer_key) FROM fact_subscription_events e "
            "JOIN dim_date d ON d.date_key = e.date_key "
            "WHERE e.event_type = 'new' AND d.date BETWEEN %s AND %s",
            (period_start, period_end),
        )
        return int(cur.fetchone()[0])


def get_churned_customers_count(conn, period_start: date, period_end: date) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(DISTINCT e.customer_key) FROM fact_subscription_events e "
            "JOIN dim_date d ON d.date_key = e.date_key "
            "WHERE e.event_type = 'cancellation' AND d.date BETWEEN %s AND %s",
            (period_start, period_end),
        )
        return int(cur.fetchone()[0])


def get_top_customers(conn, as_of_date: date, limit: int) -> list[dict]:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT c.customer_id, c.customer_name, SUM(s.mrr) AS mrr "
            "FROM fact_subscription_snapshot s "
            "JOIN dim_customer c ON c.customer_key = s.customer_key "
            "WHERE s.snapshot_date_key = %s AND s.subscription_status = 'active' "
            "GROUP BY c.customer_id, c.customer_name "
            "ORDER BY mrr DESC LIMIT %s",
            (_date_key(as_of_date), limit),
        )
        return cur.fetchall()


def get_subscription_event_counts(conn, period_start: date, period_end: date) -> dict[str, int]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT event_type, COUNT(*) FROM fact_subscription_events e "
            "JOIN dim_date d ON d.date_key = e.date_key "
            "WHERE d.date BETWEEN %s AND %s GROUP BY event_type",
            (period_start, period_end),
        )
        return dict(cur.fetchall())


def get_active_subscriptions_count(conn, as_of_date: date) -> int:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(DISTINCT subscription_id) FROM fact_subscription_snapshot "
            "WHERE snapshot_date_key = %s AND subscription_status = 'active'",
            (_date_key(as_of_date),),
        )
        return int(cur.fetchone()[0])


def get_sales_aggregates(conn, period_start: date, period_end: date) -> dict[str, dict]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT sales_status, COUNT(*), COALESCE(SUM(deal_amount), 0) FROM fact_sales s "
            "JOIN dim_date d ON d.date_key = s.date_key "
            "WHERE d.date BETWEEN %s AND %s GROUP BY sales_status",
            (period_start, period_end),
        )
        return {status: {"count": count, "revenue": float(revenue)} for status, count, revenue in cur.fetchall()}


def get_pipeline_aggregates(conn, as_of_date: date) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "SELECT COALESCE(SUM(amount), 0) AS pipeline_value, "
            "COALESCE(SUM(weighted_amount), 0) AS weighted_pipeline, "
            "COUNT(*) AS open_opportunities "
            "FROM fact_pipeline_snapshot "
            "WHERE snapshot_date_key = %s AND pipeline_status = 'open'",
            (_date_key(as_of_date),),
        )
        return cur.fetchone()


def get_revenue_trend(conn, start_date: date, end_date: date, interval: str) -> list[dict]:
    """MRR as of the last day of each bucket (not summed across days in the
    bucket — a month's "MRR" is a point-in-time snapshot, not a total)."""
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            "WITH daily_mrr AS ("
            "  SELECT d.date, date_trunc(%s, d.date)::date AS period_start, SUM(s.mrr) AS mrr "
            "  FROM fact_subscription_snapshot s "
            "  JOIN dim_date d ON d.date_key = s.snapshot_date_key "
            "  WHERE d.date BETWEEN %s AND %s AND s.subscription_status = 'active' "
            "  GROUP BY d.date, period_start"
            "), ranked AS ("
            "  SELECT period_start, mrr, "
            "         ROW_NUMBER() OVER (PARTITION BY period_start ORDER BY date DESC) AS rn "
            "  FROM daily_mrr"
            ") "
            "SELECT period_start, mrr FROM ranked WHERE rn = 1 ORDER BY period_start",
            (interval, start_date, end_date),
        )
        return cur.fetchall()


def get_revenue_breakdown(conn, period_end: date, dimension: str) -> list[dict]:
    table, key_col, label_col = _DIMENSION_MAP[dimension]
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            f"SELECT dim.{label_col} AS label, SUM(s.mrr) AS mrr "
            f"FROM fact_subscription_snapshot s "
            f"JOIN {table} dim ON dim.{key_col} = s.{key_col} "
            f"WHERE s.snapshot_date_key = %s AND s.subscription_status = 'active' "
            f"GROUP BY dim.{label_col} ORDER BY mrr DESC",
            (_date_key(period_end),),
        )
        return cur.fetchall()
