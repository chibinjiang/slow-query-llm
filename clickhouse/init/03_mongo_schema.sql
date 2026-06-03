CREATE TABLE IF NOT EXISTS slow_query_db.mongo_profile_events
(
    `id` UUID DEFAULT generateUUIDv4(),
    `db_name` String,
    `collection_name` String,
    `namespace` String,
    `operation_type` LowCardinality(String),
    `query_hash` String,
    `fingerprint` String,
    `millis` UInt32,
    `docs_examined` UInt64,
    `keys_examined` UInt64,
    `n_returned` UInt64,
    `plan_summary` String,
    `query_filter` String,
    `sort_json` String,
    `projection_json` String,
    `pipeline_json` String,
    `ts` DateTime64(3),
    `raw_profile_json` String,
    `collected_at` DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(ts)
ORDER BY (db_name, collection_name, operation_type, ts);

CREATE TABLE IF NOT EXISTS slow_query_db.mongo_ai_analysis
(
    `id` UUID DEFAULT generateUUIDv4(),
    `db_type` LowCardinality(String) DEFAULT 'mongodb',
    `db_name` String,
    `collection_name` String,
    `namespace` String,
    `operation_type` LowCardinality(String),
    `fingerprint` String,
    `sample_query` String,
    `millis` UInt32,
    `docs_examined` UInt64,
    `keys_examined` UInt64,
    `n_returned` UInt64,
    `plan_summary` String,
    `risk_level` LowCardinality(String),
    `summary` String,
    `root_cause` String,
    `optimization_suggestion` String,
    `optimized_query` String,
    `index_suggestion` String,
    `estimated_improvement` String,
    `explain_json` String,
    `model_name` LowCardinality(String),
    `prompt_version` LowCardinality(String),
    `analyzed_at` DateTime DEFAULT now()
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(analyzed_at)
ORDER BY (db_name, collection_name, fingerprint, analyzed_at);