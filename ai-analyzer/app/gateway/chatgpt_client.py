# app/gateway/chatgpt_client.py
from __future__ import annotations

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import settings
from schemas import AIAnalysisResult, SlowQueryCandidate, SlowQueryAnalysisLLMOutput


def build_prompt(candidate: SlowQueryCandidate, explain_json: str) -> str:
    """
    构造给模型的输入文本。

    这里尽量只放“结构化信息 + SQL 本体 + 执行计划”。
    不要把无关日志原文全部丢进去，否则会增加噪音。
    """
    return f"""
请分析这条 MySQL 慢查询，并输出结构化结果。

要求：
1. 只给出可落库的结果。
2. 优先从索引、扫描行数、回表、排序、聚合、SELECT * 等角度分析。
3. 如果信息不足，给出合理推断，但不要编造表结构。
4. optimized_sql 尽量给出可执行的优化版本。
5. 语言简洁、专业、可直接用于 DBA 评审。

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
    基于 LangChain 的 OpenAI 分析器。

    核心特征：
    - 使用 ChatOpenAI
    - 使用 invoke()
    - 使用 with_structured_output() 约束输出结构
    """

    def __init__(self) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is missing")

        # LangChain 官方推荐通过 langchain-openai 包使用 ChatOpenAI。
        # 这里直接指定 gpt-4.1-mini。
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
        )

        # 让模型直接返回符合 Pydantic schema 的结构化结果。
        # 对 OpenAI 来说，method="json_schema" 会使用原生结构化输出能力。
        self.structured_llm = self.llm.with_structured_output(
            SlowQueryAnalysisLLMOutput,
            method="json_schema",
        )

    def analyze(
        self,
        candidate: SlowQueryCandidate,
        explain_json: str = "",
    ) -> AIAnalysisResult:
        """
        调用模型完成分析，并映射成项目内统一的结果对象。
        """
        prompt = build_prompt(candidate, explain_json)
        print(f"提示词: {prompt}")
        # LangChain 的模型调用使用 invoke()
        result: SlowQueryAnalysisLLMOutput = self.structured_llm.invoke(
            [
                SystemMessage(
                    content="你是一个严格的 SQL 性能分析器，必须输出适合数据库落库的结构化结果。"
                ),
                HumanMessage(content=prompt),
            ]
        )

        return AIAnalysisResult(
            db_type=candidate.db_type,
            db_name=candidate.db_name,
            sql_fingerprint=candidate.sql_fingerprint,
            sample_sql=candidate.sample_sql,
            execution_count=candidate.execution_count,
            total_time_sec=candidate.total_time_sec,
            max_time_sec=candidate.max_time_sec,
            risk_level=result.risk_level,
            summary=result.summary,
            root_cause=result.root_cause,
            optimization_suggestion=result.optimization_suggestion,
            optimized_sql=result.optimized_sql,
            index_suggestion=result.index_suggestion,
            estimated_improvement=result.estimated_improvement,
            explain_json=explain_json or "",
            model_name="gpt-4.1-mini",
            prompt_version=settings.openai_prompt_version,
        )