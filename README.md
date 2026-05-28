# slow-query-llm (SQL)

> A lightweight MySQL slow query observability stack powered by Vector, ClickHouse, and Metabase.

```text
MySQL slow.log
        ↓
     Vector
(Log parsing & ETL)
        ↓
   ClickHouse
(Analytics Storage)
        ↓
    Metabase
 (Visualization)
```

---

# ✨ Features

* 🚀 One-command startup with Docker Compose
* 📦 No need to deploy MySQL inside the project
* 🔍 Parse MySQL slow query logs into structured data
* ⚡ High-performance analytics powered by ClickHouse
* 📊 Ready for Metabase dashboards
* 🧠 SQL fingerprint aggregation
* 🕒 Hourly materialized view for fast BI queries
* 🔧 Easy to extend to PostgreSQL or multi-instance databases

---

# 🏗 Architecture

```text
                  ┌──────────────────┐
                  │   MySQL Server   │
                  │  (Existing DB)   │
                  └────────┬─────────┘
                           │
                     slow.log file
                           │
                           ▼
                  ┌──────────────────┐
                  │      Vector      │
                  │ Parse / Normalize│
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │   ClickHouse     │
                  │ Analytics Engine │
                  └────────┬─────────┘
                           │
                           ▼
                  ┌──────────────────┐
                  │     Metabase     │
                  │ Visualization BI │
                  └──────────────────┘
```

---

# 📦 Tech Stack

| Component      | Purpose                         |
| -------------- | ------------------------------- |
| Vector         | Log collection & transformation |
| ClickHouse     | OLAP analytics database         |
| Metabase       | Visualization & dashboard       |
| Docker Compose | One-command deployment          |

---

# 📁 Project Structure

```text
slow-query-llm
├── docker-compose.yml
├── .env.example
├── vector
│   └── vector.toml
├── clickhouse
│   └── init
│       └── 01_create_tables.sql
├── metabase
│   └── Dockerfile
└── docs
    └── queries.md
```

---

# 🚀 Quick Start

## 1. Clone Project

```bash
git clone https://github.com/your-name/slow-query-llm.git

cd slow-query-llm
```

---

## 2. Configure Environment Variables

Copy the example config:

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Path to your existing MySQL slow query log
MYSQL_SLOW_LOG_HOST_PATH=/absolute/path/to/slow.log

CLICKHOUSE_DB=slow_query_db
CLICKHOUSE_USER=admin
CLICKHOUSE_PASSWORD=change_me

MB_TIMEZONE=Asia/Shanghai
```

---

# ⚠️ Important

This project does **NOT** deploy MySQL itself.

You must already have:

* A running MySQL instance
* Slow query log enabled
* `slow.log` continuously written to disk

Example MySQL settings:

```ini
slow_query_log = ON
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1
log_queries_not_using_indexes = ON
```

---

## 3. Start Everything

```bash
docker compose up -d
```

---

# ✅ Verify Services

## ClickHouse

```bash
curl http://localhost:8123
```

Expected output:

```text
Ok.
```

---

## Metabase

Open:

```text
http://localhost:3000
```

Complete the onboarding wizard.

---

# 📊 Connect Metabase to ClickHouse

Use these settings:

| Field    | Value         |
| -------- | ------------- |
| Host     | clickhouse    |
| Port     | 8123          |
| Database | slow_query_db |
| Username | admin         |
| Password | your password |

---

# 🔍 What Gets Collected

The pipeline extracts fields like:

| Field           | Description          |
| --------------- | -------------------- |
| sql_text        | Original SQL         |
| sql_fingerprint | Normalized SQL       |
| total_time_sec  | Query execution time |
| rows_examined   | Rows scanned         |
| rows_sent       | Rows returned        |
| collected_at    | Collection timestamp |

---

# 🧠 SQL Fingerprinting

Example:

Original SQL:

```sql
SELECT * FROM user WHERE id = 1;
SELECT * FROM user WHERE id = 2;
```

Normalized:

```sql
SELECT * FROM user WHERE id = ?;
```

This allows aggregation of similar queries.

---

# ⚡ Why ClickHouse?

Slow query analysis is fundamentally an OLAP workload:

* Aggregations
* TopN analysis
* Time-series trends
* Long-term retention

ClickHouse performs extremely well for these scenarios.

---

# 📈 Recommended Dashboards

## 1. Slow Query Trend (24h)

Metrics:

* total executions
* total query time
* max query time

---

## 2. Top Slow SQL

Group by:

* sql_fingerprint

Sort by:

* total execution time

---

## 3. Database Hotspots

Group by:

* db_host
* db_name

---

## 4. High Scan Queries

Sort by:

* rows_examined

---

# 🧩 How Vector Works

Vector handles:

1. Multi-line slow log parsing
2. Regex extraction
3. Schema normalization
4. ClickHouse ingestion

Pipeline:

```text
slow.log
   ↓
multiline merge
   ↓
regex parsing
   ↓
structured JSON
   ↓
ClickHouse
```

---

# 🛠 Materialized View

The project automatically creates:

```text
slow_queries_hourly_mv
```

Purpose:

* Faster dashboard queries
* Pre-aggregated hourly metrics
* Reduced ClickHouse scan cost

---

# 🔐 Security Notes

Before production usage:

* Replace default passwords
* Restrict ClickHouse network exposure
* Add authentication / reverse proxy
* Configure retention policies

---

# 📌 Future Roadmap

* [ ] PostgreSQL support
* [ ] Slack / WeCom alerting
* [ ] LLM-based SQL optimization suggestions
* [ ] AI slow-query classification
* [ ] Kubernetes deployment
* [ ] Multi-instance support
* [ ] Query plan analysis

---

# 🤝 Contributing

PRs and issues are welcome.

If you find this project useful, feel free to star the repository ⭐

---

# 📄 License

MIT License

---

# 🙌 Inspiration

This project was built to provide:

* lightweight observability
* low-cost SQL analytics
* simple deployment
* extensible architecture

without introducing heavyweight enterprise monitoring systems.
