# app/analyzer.py
from __future__ import annotations

from dataclasses import dataclass

from database.ch import ClickHouseRepo
from database.mysql import explain_sql
from gateway.chatgpt_client import OpenAIAnalyzer


@dataclass
class RunSummary:
    """
    一次分析任务的执行统计。
    """
    scanned: int
    analyzed: int
    skipped: int
    failed: int


class SlowQueryAnalyzerService:
    """
    慢查询 AI 分析服务。

    这里是业务编排层：
    - 取数据
    - 去重
    - 执行 EXPLAIN
    - 调 OpenAI
    - 写入 ClickHouse
    """

    def __init__(self) -> None:
        self.repo = ClickHouseRepo()
        self.llm = OpenAIAnalyzer()

    def run_once(self, days: int = 7, limit: int = 20) -> RunSummary:
        """
        扫描最近 days 天内最值得分析的慢查询，最多处理 limit 条。
        """
        candidates = self.repo.get_candidates(days=days, limit=limit)
        analyzed_keys = self.repo.get_recently_analyzed_keys(days=days)

        scanned = len(candidates)
        analyzed = 0
        skipped = 0
        failed = 0

        for candidate in candidates:
            key = (candidate.db_type, candidate.db_name, candidate.sql_fingerprint)

            # 近期分析过的 SQL 直接跳过，避免重复消耗 OpenAI 调用次数。
            if key in analyzed_keys:
                skipped += 1
                continue

            try:
                # 优先把执行计划交给模型，这样分析质量更高。
                ex_json = explain_sql(candidate.sample_sql, candidate.db_name)

                # 调用大模型生成结构化建议。
                result = self.llm.analyze(candidate, explain_json=ex_json)

                # 回写 ClickHouse，供 Metabase 和 API 查询。
                self.repo.insert_analysis(result)

                analyzed += 1
            except Exception:
                # 这里先做最小化容错。
                # 后续你可以改成日志记录、重试、死信队列等。
                failed += 1

        return RunSummary(
            scanned=scanned,
            analyzed=analyzed,
            skipped=skipped,
            failed=failed,
        )