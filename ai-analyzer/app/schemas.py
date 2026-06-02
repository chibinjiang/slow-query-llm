# app/schemas.py
from pydantic import BaseModel


class SlowQueryCandidate(BaseModel):
    """
    ClickHouse 中挑出来、准备发给 AI 分析的慢查询候选项。
    """
    db_type: str
    db_name: str
    sql_fingerprint: str
    sample_sql: str
    execution_count: int
    total_time_sec: float
    max_time_sec: float


class AIAnalysisResult(BaseModel):
    """
    AI 输出的结构化分析结果。

    这个对象会被：
    1. 写入 ClickHouse
    2. 返回给前端
    3. 在 Metabase 中做可视化
    """
    db_type: str
    db_name: str
    sql_fingerprint: str
    sample_sql: str

    execution_count: int
    total_time_sec: float
    max_time_sec: float

    risk_level: str
    summary: str
    root_cause: str
    optimization_suggestion: str
    optimized_sql: str
    index_suggestion: str
    estimated_improvement: str

    explain_json: str = ""
    model_name: str = ""
    prompt_version: str = ""