from unittest.mock import Mock

import pytest

from schemas import SlowQueryCandidate, AIAnalysisResult


@pytest.fixture
def sample_candidate():
    return SlowQueryCandidate(
        db_type="mysql",
        db_name="employees",
        sql_fingerprint="select_*_from_user_where_id=?",
        sample_sql="select * from user where id = 123",
        execution_count=100,
        total_time_sec=56.2,
        max_time_sec=5.1,
    )


@pytest.fixture
def sample_analysis_result():
    return AIAnalysisResult(
        db_type="mysql",
        db_name="employees",
        sql_fingerprint="select_*_from_user_where_id=?",
        sample_sql="select * from user where id = 123",

        execution_count=100,
        total_time_sec=56.2,
        max_time_sec=5.1,

        risk_level="HIGH",
        summary="全表扫描",
        root_cause="未命中索引",
        optimization_suggestion="增加索引",
        optimized_sql="select id,name from user where id=?",
        index_suggestion="create index idx_user_id on user(id)",
        estimated_improvement="90%",
    )