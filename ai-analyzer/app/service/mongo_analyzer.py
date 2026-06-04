# service/mongo_analyzer.py
from __future__ import annotations

import logging

from database.ch import ClickHouseRepo
from database.mongodb import MongoRepo
from gateway.chatgpt_client import OpenAIAnalyzer

logger = logging.getLogger(__name__)


class MongoSlowQueryAnalyzerService:
    """
    MongoDB 慢查询 AI 分析服务。

    职责：
    1. 从 ClickHouse 找出最值得分析的 MongoDB 慢操作
    2. 可选生成 explain
    3. 调用 LLM 生成结构化建议
    4. 写回 ClickHouse
    """

    def __init__(self) -> None:
        self.ch_repo = ClickHouseRepo()
        self.mongo_repo = MongoRepo()
        self.llm = OpenAIAnalyzer()

    def run_once(self, days: int = 7, limit: int = 20) -> dict[str, int]:
        logger.info("mongo analyzer start days=%s limit=%s", days, limit)

        candidates = self.ch_repo.get_mongo_candidates(days=days, limit=limit)
        analyzed_keys = self.ch_repo.get_recently_analyzed_mongo_keys(days=days)

        scanned = len(candidates)
        analyzed = 0
        skipped = 0
        failed = 0

        for candidate in candidates:
            key = (candidate.db_name, candidate.collection_name, candidate.fingerprint)
            if key in analyzed_keys:
                skipped += 1
                continue

            try:
                explain_json = self.mongo_repo.build_explain(candidate)
                result = self.llm.analyze_mongo(candidate, explain_json=explain_json)
                self.ch_repo.insert_mongo_analysis(result)
                analyzed += 1
            except Exception:
                logger.exception(
                    "mongo analyze failed db=%s collection=%s fingerprint=%s",
                    candidate.db_name,
                    candidate.collection_name,
                    candidate.fingerprint,
                )
                failed += 1

        logger.info(
            "mongo analyzer finished scanned=%s analyzed=%s skipped=%s failed=%s",
            scanned, analyzed, skipped, failed,
        )
        return {
            "scanned": scanned,
            "analyzed": analyzed,
            "skipped": skipped,
            "failed": failed,
        }