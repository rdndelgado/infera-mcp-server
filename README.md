# infera-mcp-server

Lets an AI assistant like Claude or ChatGPT access your company's internal database and give you insights — with controlled access, only to what it needs.

## Architecture

![Infera MCP Server architecture](./assets/mcp-server.png)

## Company records it can pull up

- **Customers** — who they are, when they joined, and whether they're active, churned, or a prospect.
- **Subscriptions & plans** — what each customer is subscribed to, and every upgrade, downgrade, or cancellation along the way.
- **Sales deals** — every closed deal, won or lost.
- **Sales pipeline** — every open opportunity still being worked.

## Available MCP tools

| Tool | What it does |
|---|---|
| `get_business_summary` | Gives a quick health check of the business — revenue, customers, churn, and sales in one snapshot. |
| `compare_periods` | Compares how the business performed between two time periods, side by side. |
| `get_revenue_metrics` | Shows recurring revenue and where the growth or loss came from. |
| `get_revenue_trend` | Tracks recurring revenue over time — by day, month, or quarter. |
| `get_revenue_breakdown` | Shows which customers, plans, or products are driving the most revenue. |
| `get_customer_metrics` | Counts customers gained, lost, and kept, plus overall growth rate. |
| `get_top_customers` | Lists the biggest customers, ranked by how much they pay. |
| `get_subscription_metrics` | Tracks subscription activity — new signups, upgrades, downgrades, cancellations. |
| `get_churn_metrics` | Measures how much revenue and how many customers are being lost, and how well existing ones are retained. |
| `get_sales_metrics` | Summarizes closed deals — how many were won or lost, and how big they were on average. |
| `get_sales_pipeline` | Shows what deals are still open and roughly how much they could be worth. |

## Sample analytical questions

- What's our monthly recurring revenue right now, and is our cash flow trending up or down?
- Who are our top customers, and which ones are we at risk of losing?
- How much revenue is sitting in open deals, and how likely are they to close?
- Are we losing customers faster than we're signing new ones this month?
- What's our sales win rate, and how big are deals closing on average?

## Potential integrations

Not yet built — natural next steps beyond read-only reporting:

- **Calendar** — read schedules, create meeting events (book a call with an at-risk customer, schedule the board update).
- **Email** — read inbox, send new emails, reply to threads (follow up a stalled deal, send the monthly digest).
- **Slack** — same as email: read channels/DMs, send messages, reply in-thread.
- **CRM** — another database, but for customer/deal records (HubSpot/Salesforce) — read and write, alongside the analytical warehouse.

Once wired in, this unlocks questions like: "How many leads do we have, how many have we contacted, how many replied, and what platform is each one in (email vs. Slack vs. CRM)?"

## Setup (Docker)

Run MCP Server and Postgres Database Engine locally using Docker

```bash
cp .env.example .env
docker compose up -d --build
docker compose run --rm mcp python -m warehouse.seed.load
```

Once the container's running, connect it to Claude Code by typing this on terminal:

```bash
claude mcp add infera --transport http http://localhost:8000 --header "Authorization: Bearer <MCP_API_KEY>"
```

Use the same `MCP_API_KEY` value set in `.env`.