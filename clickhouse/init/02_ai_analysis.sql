CREATE TABLE IF NOT EXISTS slow_query_db.slow_query_ai_analysis
(
    `id` UUID DEFAULT generateUUIDv4(),
    `db_type` LowCardinality(String),
    `db_name` String,
    `sql_fingerprint` String,
    `sample_sql` String,
    `execution_count` UInt64,
    `total_time_sec` Float64,
    `max_time_sec` Float64,
    `risk_level` LowCardinality(String),
    `summary` String,
    `root_cause` String,
    `optimization_suggestion` String,
    `optimized_sql` String,
    `index_suggestion` String,
    `estimated_improvement` String,
    `explain_json` String,
    `model_name` LowCardinality(String),
    `prompt_version` LowCardinality(String),
    `analyzed_at` DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(analyzed_at)
ORDER BY (db_type, db_name, sql_fingerprint, analyzed_at);