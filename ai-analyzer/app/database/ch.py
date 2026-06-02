"""
app/clickhouse_repo.py 这个文件只管和 ClickHouse 打交道，不掺杂别的逻辑。
"""
from __future__ import annotations

from typing import Any

import clickhouse_connect

from .config import settings
from .schemas import AIAnalysisResult, SlowQueryCandidate


class ClickHouseRepo:
    """
    ClickHouse 数据访问层。

    职责很单一：
    - 读取慢查询候选
    - 读取已分析记录
    - 写入 AI 分析结果
    - 提供前端展示用的数据
    """

    def __init__(self) -> None:
        self.client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_db,
        )

    def get_candidates(self, days: int = 7, limit: int = 20) -> list[SlowQueryCandidate]:
        """
        从物化视图里挑选最近一段时间内最值得分析的慢查询。

        这里默认按 total_time 排序，优先分析“累计耗时最高”的 SQL。
        """
        sql = f"""
        SELECT
            db_type,
            db_name,
            sql_fingerprint,
            any(sample_sql) AS sample_sql,
            sum(total_executions) AS execution_count,
            sum(total_time) AS total_time_sec,
            max(max_time) AS max_time_sec
        FROM {settings.clickhouse_db}.slow_queries_hourly_mv
        WHERE hour >= now() - INTERVAL {days} DAY
        GROUP BY db_type, db_name, sql_fingerprint
        ORDER BY total_time_sec DESC
        LIMIT {limit}
        """
        rows = self.client.query(sql).result_rows

        return [
            SlowQueryCandidate(
                db_type=row[0],
                db_name=row[1],
                sql_fingerprint=row[2],
                sample_sql=row[3] or "",
                execution_count=int(row[4] or 0),
                total_time_sec=float(row[5] or 0),
                max_time_sec=float(row[6] or 0),
            )
            for row in rows
        ]

    def get_recently_analyzed_keys(self, days: int = 7) -> set[tuple[str, str, str]]:
        """
        查询最近已经分析过的 SQL 指纹。

        这样做可以避免同一条 SQL 在短时间内被重复送给 OpenAI，
        也能明显控制成本。
        """
        sql = f"""
        SELECT
            db_type,
            db_name,
            sql_fingerprint
        FROM {settings.clickhouse_db}.slow_query_ai_analysis
        WHERE analyzed_at >= now() - INTERVAL {days} DAY
        GROUP BY db_type, db_name, sql_fingerprint
        """
        rows = self.client.query(sql).result_rows
        return {(r[0], r[1], r[2]) for r in rows}

    def insert_analysis(self, item: AIAnalysisResult) -> None:
        """
        把 AI 分析结果写回 ClickHouse。

        这样 Metabase 就能直接读这张表做展示。
        """
        self.client.insert(
            f"{settings.clickhouse_db}.slow_query_ai_analysis",
            [[
                item.db_type,
                item.db_name,
                item.sql_fingerprint,
                item.sample_sql,
                item.execution_count,
                item.total_time_sec,
                item.max_time_sec,
                item.risk_level,
                item.summary,
                item.root_cause,
                item.optimization_suggestion,
                item.optimized_sql,
                item.index_suggestion,
                item.estimated_improvement,
                item.explain_json,
                item.model_name,
                item.prompt_version,
            ]],
            column_names=[
                "db_type",
                "db_name",
                "sql_fingerprint",
                "sample_sql",
                "execution_count",
                "total_time_sec",
                "max_time_sec",
                "risk_level",
                "summary",
                "root_cause",
                "optimization_suggestion",
                "optimized_sql",
                "index_suggestion",
                "estimated_improvement",
                "explain_json",
                "model_name",
                "prompt_version",
            ],
        )

    def list_latest_analyses(self, limit: int = 20) -> list[dict[str, Any]]:
        """
        给前端页面使用，返回最新的分析摘要。
        """
        sql = f"""
        SELECT
            db_type,
            db_name,
            sql_fingerprint,
            any(sample_sql) AS sample_sql,
            any(risk_level) AS risk_level,
            any(summary) AS summary,
            any(root_cause) AS root_cause,
            any(optimization_suggestion) AS optimization_suggestion,
            any(optimized_sql) AS optimized_sql,
            any(index_suggestion) AS index_suggestion,
            any(estimated_improvement) AS estimated_improvement,
            max(analyzed_at) AS analyzed_at
        FROM {settings.clickhouse_db}.slow_query_ai_analysis
        GROUP BY db_type, db_name, sql_fingerprint
        ORDER BY analyzed_at DESC
        LIMIT {limit}
        """
        cols = [
            "db_type",
            "db_name",
            "sql_fingerprint",
            "sample_sql",
            "risk_level",
            "summary",
            "root_cause",
            "optimization_suggestion",
            "optimized_sql",
            "index_suggestion",
            "estimated_improvement",
            "analyzed_at",
        ]
        rows = self.client.query(sql).result_rows
        return [dict(zip(cols, row)) for row in rows]

    def get_analysis_detail(self, db_type: str, db_name: str, sql_fingerprint: str) -> list[dict[str, Any]]:
        """
        查询某个 SQL 指纹的完整历史分析记录。
        """
        sql = f"""
        SELECT
            db_type,
            db_name,
            sql_fingerprint,
            sample_sql,
            execution_count,
            total_time_sec,
            max_time_sec,
            risk_level,
            summary,
            root_cause,
            optimization_suggestion,
            optimized_sql,
            index_suggestion,
            estimated_improvement,
            explain_json,
            model_name,
            prompt_version,
            analyzed_at
        FROM {settings.clickhouse_db}.slow_query_ai_analysis
        WHERE db_type = %(db_type)s
          AND db_name = %(db_name)s
          AND sql_fingerprint = %(sql_fingerprint)s
        ORDER BY analyzed_at DESC
        """
        result = self.client.query(
            sql,
            parameters={
                "db_type": db_type,
                "db_name": db_name,
                "sql_fingerprint": sql_fingerprint,
            },
        )
        return result.result_rows