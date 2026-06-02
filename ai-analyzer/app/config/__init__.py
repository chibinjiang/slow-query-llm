from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 以当前文件所在目录向上推一层，作为项目根目录。
# 这样无论你在本地跑，还是在 Docker 容器里跑，都能稳定找到 .env。
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# 读取 .env 文件中的变量。
# 注意：环境变量本身仍然可以覆盖 .env 中的值。
load_dotenv(dotenv_path=ENV_FILE, override=False)


def _env_bool(name: str, default: str = "false") -> bool:
    """
    把环境变量里的字符串转成布尔值。

    例如：
    ENABLE_MYSQL_EXPLAIN=true
    ENABLE_MYSQL_EXPLAIN=1
    ENABLE_MYSQL_EXPLAIN=yes
    都会被识别为 True。
    """
    value = os.getenv(name, default).strip().lower()
    return value in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    """
    集中管理整个 ai-analyzer 服务的配置。

    这样做的好处是：
    1. 代码里不散落 os.getenv()
    2. 后续增加新配置时只改这里
    3. 更容易测试和维护
    """

    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    openai_prompt_version: str = os.getenv("OPENAI_PROMPT_VERSION", "v1")

    # ClickHouse
    clickhouse_host: str = os.getenv("CLICKHOUSE_HOST", "clickhouse")
    clickhouse_port: int = int(os.getenv("CLICKHOUSE_PORT", "8123"))
    clickhouse_db: str = os.getenv("CLICKHOUSE_DB", "slow_query_db")
    clickhouse_user: str = os.getenv("CLICKHOUSE_USER", "admin")
    clickhouse_password: str = os.getenv("CLICKHOUSE_PASSWORD", "")

    # MySQL
    enable_mysql_explain: bool = _env_bool("ENABLE_MYSQL_EXPLAIN", "true")
    mysql_host: str = os.getenv("MYSQL_HOST", "mysql")
    mysql_port: int = int(os.getenv("MYSQL_PORT", "3306"))
    mysql_user: str = os.getenv("MYSQL_USER", "root")
    mysql_password: str = os.getenv("MYSQL_PASSWORD", "")


settings = Settings()