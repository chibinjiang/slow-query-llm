# app/openai_client.py
from __future__ import annotations
import json
from openai import OpenAI

from config import settings
from schemas import AIAnalysisResult, SlowQueryCandidate

# 约束模型输出结构。
# 这样做的好处是：返回结果可以直接落库，不用再写一层复杂的文本解析。
SCHEMA = {
    "type": "object",
    "properties": {
        "risk_level": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"],
        },
        "summary": {"type": "string"},
        "root_cause": {"type": "string"},
        "optimization_suggestion": {"type": "string"},
        "optimized_sql": {"type": "string"},
        "index_suggestion": {"type": "string"},
        "estimated_improvement": {"type": "string"},
    },
    "required": [
        "risk_level",
        "summary",
        "root_cause",
        "optimization_suggestion",
        "optimized_sql",
        "index_suggestion",
        "estimated_improvement",
    ],
    "additionalProperties": False,
}


def build_prompt(candidate: SlowQueryCandidate, explain_json: str) -> str:
    """
    把 AI 分析所需的信息拼成一个清晰的 prompt。

    注意：
    - 不要把整个慢日志原样塞给模型
    - 最好只给结构化信息、SQL 本体、执行计划
    - 输入越干净，模型输出越稳定
    """
    return f"""
你是一名资深 MySQL DBA 和 SQL 性能优化专家。

请分析下面这条慢查询，并给出可落库的结构化结果。

要求：
1. 只输出符合 JSON Schema 的结果，不要输出多余文本。
2. 优化建议要务实，优先考虑索引、改写 SQL、减少扫描行数、避免 SELECT *、限制返回行数。
3. 如果 SQL 已经比较合理，也要指出为什么慢，不能空泛。
4. optimized_sql 必须尽量给出一个可执行的优化版本。
5. 不要编造不存在的表结构信息；如果信息不足，请基于现有 SQL 和执行计划做最合理推断。

慢查询信息：
- db_type: {candidate.db_type}
- db_name: {candidate.db_name}
- sql_fingerprint: {candidate.sql_fingerprint}
- execution_count: {candidate.execution_count}
- total_time_sec: {candidate.total_time_sec}
- max_time_sec: {candidate.max_time_sec}

原始 SQL：
{candidate.sample_sql}

EXPLAIN FORMAT=JSON：
{explain_json if explain_json else "EMPTY"}
""".strip()


class OpenAIAnalyzer:
    """
    OpenAI 分析器。

    只做一件事：
    把慢查询候选项转成结构化分析结果。
    """

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")

        self.client = OpenAI(api_key=settings.openai_api_key)

    def analyze(self, candidate: SlowQueryCandidate, explain_json: str = "") -> AIAnalysisResult:
        """
        调用模型并解析结果。
        """
        prompt = build_prompt(candidate, explain_json)

        response = self.client.responses.create(
            model=settings.openai_model,
            instructions="你是一个严格的 SQL 性能分析器。必须按 JSON Schema 返回结果。",
            input=prompt,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "slow_query_analysis",
                    "strict": True,
                    "schema": SCHEMA,
                },
            },
        )

        payload = json.loads(response.output_text)

        return AIAnalysisResult(
            db_type=candidate.db_type,
            db_name=candidate.db_name,
            sql_fingerprint=candidate.sql_fingerprint,
            sample_sql=candidate.sample_sql,
            execution_count=candidate.execution_count,
            total_time_sec=candidate.total_time_sec,
            max_time_sec=candidate.max_time_sec,
            risk_level=payload["risk_level"],
            summary=payload["summary"],
            root_cause=payload["root_cause"],
            optimization_suggestion=payload["optimization_suggestion"],
            optimized_sql=payload["optimized_sql"],
            index_suggestion=payload["index_suggestion"],
            estimated_improvement=payload["estimated_improvement"],
            explain_json=explain_json or "",
            model_name=settings.openai_model,
            prompt_version=settings.openai_prompt_version,
        )