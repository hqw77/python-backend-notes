"""日志配置.

目标: 每条日志都能回答三个问题
    什么时候发生的  -> 时间戳
    是哪个请求的    -> [request_id]
    哪个模块打的    -> logger 名字

request_id 用 contextvar 传, 不用全局变量:
    全局变量在并发下会被别的请求覆盖(见 fastapi_notes ch05 案例 2).
"""

import logging
import sys
from contextvars import ContextVar

# 默认 "-" 表示"不在请求里"(比如定时任务, 启动阶段)
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

LOG_FORMAT = "%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s"


class RequestIdFilter(logging.Filter):
    """给每条日志补上 request_id 字段."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


def setup_logging(level: int = logging.INFO) -> None:
    """配置根 logger. 重复调用是安全的(用标记位去重)."""
    root = logging.getLogger()

    if any(getattr(handler, "_app_handler", False) for handler in root.handlers):
        return

    handler = logging.StreamHandler(sys.stdout)
    handler._app_handler = True          # 自定义标记, 用于判断是否已经加过
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handler.addFilter(RequestIdFilter())

    root.addHandler(handler)
    root.setLevel(level)

    # 第三方库的 INFO 日志太吵(每发一次 HTTP 请求就打一行), 压到 WARNING
    for noisy in ("httpx", "httpcore", "urllib3"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
