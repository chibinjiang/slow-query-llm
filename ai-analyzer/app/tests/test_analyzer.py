from unittest.mock import Mock

from service.analyzer import SlowQueryAnalyzerService

def test_run_once_success(
    mocker,
    sample_candidate,
    sample_analysis_result,
):
    """
    正常分析流程
    """

    service = SlowQueryAnalyzerService()

    service.repo = Mock()
    service.llm = Mock()

    service.repo.get_candidates.return_value = [
        sample_candidate
    ]

    service.repo.get_recently_analyzed_keys.return_value = set()

    mocker.patch(
        "app.analyzer.explain_sql",
        return_value='{"query_block":{}}'
    )

    service.llm.analyze.return_value = (
        sample_analysis_result
    )

    result = service.run_once()

    assert result.scanned == 1
    assert result.analyzed == 1
    assert result.skipped == 0
    assert result.failed == 0

    service.repo.insert_analysis.assert_called_once()


def test_run_once_skip_existing(
    sample_candidate,
):
    """
    已分析SQL直接跳过
    """

    service = SlowQueryAnalyzerService()

    service.repo = Mock()
    service.llm = Mock()

    service.repo.get_candidates.return_value = [
        sample_candidate
    ]

    service.repo.get_recently_analyzed_keys.return_value = {
        (
            sample_candidate.db_type,
            sample_candidate.db_name,
            sample_candidate.sql_fingerprint,
        )
    }

    result = service.run_once()

    assert result.scanned == 1
    assert result.skipped == 1
    assert result.analyzed == 0

    service.llm.analyze.assert_not_called()

def test_run_once_openai_exception(
    mocker,
    sample_candidate,
):
    """
    OpenAI报错
    """

    service = SlowQueryAnalyzerService()

    service.repo = Mock()
    service.llm = Mock()

    service.repo.get_candidates.return_value = [
        sample_candidate
    ]

    service.repo.get_recently_analyzed_keys.return_value = set()

    mocker.patch(
        "app.analyzer.explain_sql",
        return_value="{}",
    )

    service.llm.analyze.side_effect = Exception(
        "OpenAI timeout"
    )

    result = service.run_once()

    assert result.failed == 1
    assert result.analyzed == 0

def test_run_once_insert_failed(
    mocker,
    sample_candidate,
    sample_analysis_result,
):
    """
    ClickHouse写入失败
    """

    service = SlowQueryAnalyzerService()

    service.repo = Mock()
    service.llm = Mock()

    service.repo.get_candidates.return_value = [
        sample_candidate
    ]

    service.repo.get_recently_analyzed_keys.return_value = set()

    mocker.patch(
        "app.analyzer.explain_sql",
        return_value="{}",
    )

    service.llm.analyze.return_value = (
        sample_analysis_result
    )

    service.repo.insert_analysis.side_effect = (
        Exception("clickhouse error")
    )

    result = service.run_once()

    assert result.failed == 1


def test_run_once_no_candidates():
    """
    无慢查询
    """

    service = SlowQueryAnalyzerService()

    service.repo = Mock()
    service.llm = Mock()

    service.repo.get_candidates.return_value = []

    service.repo.get_recently_analyzed_keys.return_value = set()

    result = service.run_once()

    assert result.scanned == 0
    assert result.analyzed == 0
    assert result.failed == 0
    assert result.skipped == 0