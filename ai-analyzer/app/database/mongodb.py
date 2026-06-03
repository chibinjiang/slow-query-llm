# database/mongodb.py
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pymongo import MongoClient

from config import settings
from schemas.mongodb import MongoProfileCandidate


class MongoRepo:
    """
    MongoDB 数据访问层。

    职责：
    1. 读取 system.profile
    2. 将 profiler 文档标准化成候选记录
    3. 根据候选记录生成 explain
    4. 维护增量 watermark
    """

    def __init__(self) -> None:
        self.client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        self.db_names = [
            x.strip()
            for x in settings.mongodb_databases.split(",")
            if x.strip()
        ]
        self.watermark_file = Path(settings.mongodb_watermark_file)

    def ping(self) -> None:
        """
        确认 MongoDB 可连接。
        """
        self.client.admin.command("ping")

    def _load_watermark(self) -> datetime | None:
        """
        从本地文件读取上一次采集到的 ts。
        """
        if not self.watermark_file.exists():
            return None

        try:
            payload = json.loads(self.watermark_file.read_text(encoding="utf-8"))
            ts = payload.get("ts")
            if not ts:
                return None
            return datetime.fromisoformat(ts)
        except Exception:
            return None

    def _save_watermark(self, ts: datetime) -> None:
        """
        保存本次采集到的最新 ts。
        """
        self.watermark_file.parent.mkdir(parents=True, exist_ok=True)
        self.watermark_file.write_text(
            json.dumps({"ts": ts.isoformat()}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _safe_json(obj: Any) -> str:
        return json.dumps(obj, ensure_ascii=False, default=str, sort_keys=True)

    @staticmethod
    def _fingerprint_from_doc(doc: dict[str, Any]) -> str:
        """
        生成稳定指纹。

        优先使用 MongoDB profiler 自带的 queryHash；
        如果没有，就根据标准化后的命令内容做 hash。
        """
        query_hash = str(doc.get("queryHash") or "").strip()
        if query_hash:
            return query_hash

        command = doc.get("command") or {}
        normalized = {
            "op": doc.get("op", ""),
            "ns": doc.get("ns", ""),
            "command_name": next(iter(command.keys()), ""),
            "filter": command.get("filter") or command.get("q") or {},
            "sort": command.get("sort") or {},
            "projection": command.get("projection") or command.get("fields") or {},
            "pipeline": command.get("pipeline") or [],
        }
        raw = json.dumps(normalized, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _operation_type(doc: dict[str, Any]) -> str:
        """
        从 profiler 文档中识别操作类型。
        """
        command = doc.get("command") or {}

        if "aggregate" in command:
            return "aggregate"
        if "find" in command:
            return "find"
        if "update" in command:
            return "update"
        if "delete" in command:
            return "delete"
        if "count" in command:
            return "count"
        if "distinct" in command:
            return "distinct"
        if doc.get("op"):
            return str(doc["op"])
        return "unknown"

    @staticmethod
    def _collection_name(ns: str) -> str:
        if "." not in ns:
            return ns
        return ns.split(".", 1)[1]

    def _normalize_doc(self, db_name: str, doc: dict[str, Any]) -> MongoProfileCandidate:
        """
        把 system.profile 原始文档标准化成统一结构。
        """
        ns = str(doc.get("ns") or "")
        command = doc.get("command") or {}
        operation_type = self._operation_type(doc)
        collection_name = self._collection_name(ns)
        fingerprint = self._fingerprint_from_doc(doc)

        query_filter = command.get("filter") or command.get("q") or {}
        sort_json = command.get("sort") or {}
        projection_json = command.get("projection") or command.get("fields") or {}
        pipeline_json = command.get("pipeline") or []

        return MongoProfileCandidate(
            db_name=db_name,
            collection_name=collection_name,
            namespace=ns,
            operation_type=operation_type,
            query_hash=str(doc.get("queryHash") or ""),
            fingerprint=fingerprint,
            millis=int(doc.get("millis") or 0),
            docs_examined=int(doc.get("docsExamined") or 0),
            keys_examined=int(doc.get("keysExamined") or 0),
            n_returned=int(doc.get("nreturned") or doc.get("nReturned") or 0),
            plan_summary=str(doc.get("planSummary") or ""),
            query_filter=self._safe_json(query_filter),
            sort_json=self._safe_json(sort_json),
            projection_json=self._safe_json(projection_json),
            pipeline_json=self._safe_json(pipeline_json),
            ts=(doc.get("ts").isoformat() if doc.get("ts") else ""),
            raw_profile_json=self._safe_json(doc),
        )

    def collect_profile_candidates(
        self,
        limit_per_db: int = 500,
    ) -> tuple[list[MongoProfileCandidate], datetime | None]:
        """
        增量读取 system.profile 中的新记录。

        返回：
        - candidates: 标准化后的慢操作候选
        - newest_ts: 本次扫描到的最新时间，用于更新 watermark
        """
        last_ts = self._load_watermark()
        newest_ts = last_ts
        all_candidates: list[MongoProfileCandidate] = []

        for db_name in self.db_names:
            profile = self.client[db_name]["system.profile"]

            query: dict[str, Any] = {}
            if last_ts:
                query["ts"] = {"$gt": last_ts}

            cursor = profile.find(query).sort("ts", 1).limit(limit_per_db)

            for doc in cursor:
                candidate = self._normalize_doc(db_name, doc)
                all_candidates.append(candidate)

                if doc.get("ts"):
                    ts = doc["ts"]
                    if newest_ts is None or ts > newest_ts:
                        newest_ts = ts

        return all_candidates, newest_ts

    def save_watermark_if_needed(self, ts: datetime | None) -> None:
        """
        如果本次采集到了更晚的 ts，则更新 watermark。
        """
        if ts is None:
            return
        self._save_watermark(ts)

    def build_explain(self, candidate: MongoProfileCandidate) -> str:
        """
        针对候选操作生成 explain() 结果。

        explain 返回 queryPlanner / executionStats，
        这对判断索引使用、扫描量和执行代价非常有帮助。:contentReference[oaicite:1]{index=1}
        """
        if not settings.enable_mongodb_explain:
            return ""

        try:
            db = self.client[candidate.db_name]
            command = json.loads(candidate.raw_profile_json)
            op = candidate.operation_type

            if op == "find":
                find_cmd = command.get("command") or {}
                explain_cmd = {
                    "find": candidate.collection_name,
                    "filter": find_cmd.get("filter") or find_cmd.get("query") or {},
                }
                if find_cmd.get("sort"):
                    explain_cmd["sort"] = find_cmd["sort"]
                if find_cmd.get("projection") or find_cmd.get("fields"):
                    explain_cmd["projection"] = find_cmd.get("projection") or find_cmd.get("fields")
                if find_cmd.get("limit"):
                    explain_cmd["limit"] = find_cmd.get("limit")

                result = db.command(
                    {
                        "explain": explain_cmd,
                        "verbosity": "executionStats",
                    }
                )
                return self._safe_json(result)

            if op == "aggregate":
                agg_cmd = command.get("command") or {}
                result = db.command(
                    {
                        "explain": {
                            "aggregate": candidate.collection_name,
                            "pipeline": agg_cmd.get("pipeline") or [],
                            "cursor": {},
                        },
                        "verbosity": "executionStats",
                    }
                )
                return self._safe_json(result)

            return ""

        except Exception as exc:
            return f"EXPLAIN_FAILED: {type(exc).__name__}: {exc}"