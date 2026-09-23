"""本地/CI 测试配置：用内存 SQLite，无需启动 PostgreSQL。生产仍使用 config.settings。"""

from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
