import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    统一配置日志输出格式。

    目标：
    1. INFO 及以上级别都能输出
    2. 日志格式适合工程化排障
    3. 输出到 stdout，方便 Docker 收集
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    # handler.addFilter(ServiceContextFilter())
    handler.setFormatter(
        logging.Formatter(
            fmt=(
                "%(asctime)s | %(levelname)-5s | "
                "%(service_name)s | %(name)s | "
                "%(filename)s:%(lineno)d | "
                "trace_id=%(trace_id)s | %(message)s"
            ),
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(handler)

    # 降低一些第三方库的噪音
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("clickhouse_connect").setLevel(logging.WARNING)