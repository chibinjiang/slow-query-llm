CREATE DATABASE IF NOT EXISTS slow_query_db;

CREATE TABLE IF NOT EXISTS slow_query_db.slow_queries
(
    `id` UInt64 DEFAULT rowNumberInAllBlocks(),
    `db_type` LowCardinality(String) COMMENT 'mysql/postgresql，数据隔离关键字段',
    `db_host` String COMMENT '数据库实例地址',
    `db_name` String COMMENT '数据库名',
    `sql_fingerprint` String COMMENT 'SQL指纹，用于聚合',
    `sql_text` String COMMENT '原始SQL语句',
    `execution_count` UInt32 COMMENT '执行次数',
    `total_time_sec` Float64 COMMENT '总耗时(秒)',
    `avg_time_sec` Float64 COMMENT '平均耗时(秒)',
    `max_time_sec` Float64 COMMENT '最大耗时(秒)',
    `rows_examined` UInt64 COMMENT '扫描行数',
    `rows_sent` UInt64 COMMENT '返回行数',
    `client_ip` String COMMENT '客户端IP',
    `collected_at` DateTime DEFAULT now() COMMENT '采集时间'
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(collected_at)
ORDER BY (db_type, db_host, db_name, collected_at)
TTL collected_at + INTERVAL 90 DAY;

CREATE MATERIALIZED VIEW IF NOT EXISTS slow_query_db.slow_queries_hourly_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(hour)
ORDER BY (db_type, db_name, hour, sql_fingerprint)
AS
SELECT
    db_type,
    db_name,
    sql_fingerprint,
    any(sql_text) AS sample_sql,
    date_trunc('hour', collected_at) AS hour,
    sum(execution_count) AS total_executions,
    sum(total_time_sec) AS total_time,
    max(max_time_sec) AS max_time
FROM slow_query_db.slow_queries
GROUP BY db_type, db_name, sql_fingerprint, hour;
