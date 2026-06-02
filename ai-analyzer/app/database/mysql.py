# app/mysql_explain.py
from __future__ import annotations

import json

import mysql.connector

from .config import settings


def explain_sql(sample_sql: str, db_name: str) -> str:
    """
    对 SQL 执行 EXPLAIN FORMAT=JSON。

    为什么要这么做：
    - 只看 SQL 文本，很多时候无法判断真实性能瓶颈
    - 结合执行计划，AI 的分析会准确很多
    - 如果执行失败，也不要让整个流程中断，所以这里做了异常兜底
    """
    if not settings.enable_mysql_explain:
        return ""

    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=db_name,
            autocommit=True,
        )
        cursor = conn.cursor()
        cursor.execute(f"EXPLAIN FORMAT=JSON {sample_sql}")
        row = cursor.fetchone()
        if not row:
            return ""

        explain_raw = row[0]
        if isinstance(explain_raw, bytes):
            explain_raw = explain_raw.decode("utf-8", errors="ignore")

        if isinstance(explain_raw, str):
            return explain_raw

        return json.dumps(explain_raw, ensure_ascii=False)

    except Exception as exc:
        # 不让 EXPLAIN 失败影响整条分析链路
        return f"EXPLAIN_FAILED: {type(exc).__name__}: {exc}"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()