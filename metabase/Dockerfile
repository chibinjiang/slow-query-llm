FROM metabase/metabase:v0.61.2.8

USER root

RUN mkdir -p /plugins && \
    apt-get update && apt-get install -y --no-install-recommends wget ca-certificates && \
    rm -rf /var/lib/apt/lists/* && \
    wget -O /plugins/clickhouse.metabase-driver.jar \
      https://github.com/ClickHouse/metabase-clickhouse-driver/releases/download/1.53.4/clickhouse.metabase-driver.jar && \
    chown -R metabase:metabase /plugins

USER metabase
