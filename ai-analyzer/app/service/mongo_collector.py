# service/mongo_collector.py
from __future__ import annotations

import logging

from database.mongodb import MongoRepo
from database.ch import ClickHouseRepo
from schemas.mongodb import MongoProfileCandidate

logger = logging.getLogger(__name__)


class MongoProfileCollectorService:
    """
    MongoDB profiler 采集服务。
    MongoDB 侧启用 profiler 的命令: db.setProfilingLevel(1, { slowms: 200 })
    流程：
    1. 从 system.profile 读增量数据
    2. 标准化
    3. 写入 ClickHouse 原始表
    """

    def __init__(self):
        self.mongo_repo = MongoRepo()
        self.ch_repo = ClickHouseRepo()

    def run_once(self) -> dict[str, int]:
        logger.info("mongo collector start")

        self.mongo_repo.ping()
        candidates, newest_ts = self.mongo_repo.collect_profile_candidates()

        if not candidates:
            logger.info("mongo collector no new events")
            return {"scanned": 0, "inserted": 0}

        self.ch_repo.insert_mongo_profile_events(candidates)
        self.mongo_repo.save_watermark_if_needed(newest_ts)

        logger.info(
            "mongo collector finished scanned=%s inserted=%s",
            len(candidates),
            len(candidates),
        )
        return {"scanned": len(candidates), "inserted": len(candidates)}