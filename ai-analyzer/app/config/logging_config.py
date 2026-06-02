import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """
    配置全局日志输出。

    作用：
    - 控制日志级别
    - 让 logger.info() 也能打印
    - 统一日志格式
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # 覆盖可能已存在的默认配置
    )
