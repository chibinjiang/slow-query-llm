# Metabase 常用查询建议

## 1. 最近 24 小时慢查询趋势

数据源：`slow_queries_hourly_mv`

字段建议：

- `hour`
- `total_executions`
- `total_time`
- `max_time`

## 2. Top SQL 指纹排行

数据源：`slow_queries`

推荐维度：

- `sql_fingerprint`

推荐指标：

- `sum(total_time_sec)`
- `sum(execution_count)`
- `max(max_time_sec)`

## 3. 按数据库实例分组

推荐维度：

- `db_host`
- `db_name`

推荐指标：

- `sum(total_time_sec)`
- `count()`
- `avg(avg_time_sec)`

## 4. 原始慢日志抽样

可以直接看 `slow_queries` 表里的：

- `sql_text`
- `rows_examined`
- `rows_sent`
- `collected_at`
