# mysql.py
from __future__ import annotations

from pydantic import BaseModel, Field


class MongoProfileCandidate(BaseModel):
    """
    MongoDB profiler 中抽取出来的一条“慢操作候选”。

    这里对应 MongoDB 的 system.profile 记录。
    """
    db_type: str = "mongodb"
    db_name: str
    collection_name: str
    namespace: str
    operation_type: str  # find / aggregate / update / delete / count / getMore ...
    query_hash: str = ""
    fingerprint: str = ""

    millis: int = 0
    docs_examined: int = 0
    keys_examined: int = 0
    n_returned: int = 0
    plan_summary: str = ""

    query_filter: str = ""
    sort_json: str = ""
    projection_json: str = ""
    pipeline_json: str = ""

    ts: str = ""
    raw_profile_json: str = ""


class MongoAnalysisLLMOutput(BaseModel):
    """
    LLM 针对 MongoDB 输出的结构化结果。
    """
    risk_level: str = Field(description="LOW / MEDIUM / HIGH / CRITICAL")
    summary: str
    root_cause: str
    optimization_suggestion: str
    optimized_query: str
    index_suggestion: str
    estimated_improvement: str


class MongoAnalysisResult(BaseModel):
    """
    最终写入 ClickHouse 的 MongoDB 分析结果。
    """
    db_type: str = "mongodb"
    db_name: str
    collection_name: str
    namespace: str
    operation_type: str
    fingerprint: str
    sample_query: str

    millis: int
    docs_examined: int
    keys_examined: int
    n_returned: int
    plan_summary: str

    risk_level: str
    summary: str
    root_cause: str
    optimization_suggestion: str
    optimized_query: str
    index_suggestion: str
    estimated_improvement: str

    explain_json: str = ""
    model_name: str = ""
    prompt_version: str = ""