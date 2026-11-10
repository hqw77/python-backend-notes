"""FastAPI 第二部分 - 案例 5-1: 日志怎么配才有用.

默认的 logging 输出长这样:
    INFO:root:发送欢迎通知给 张三

问题: 没有时间, 没有级别对齐, 没有请求 id, 出问题时无法串起来.

这个案例对比三种配置:
    ① 什么都不配(默认)
    ② 自定义格式(时间 + 级别 + 模块 + 消息)
    ③ 加上请求 id(用 contextvar 自动注入)

怎么跑:
    python fastapi_notes/ch05/code/01_logging_basics.py
"""

import logging
import sys
from contextvars import ContextVar

# ------------------------------------------------------------------ ① 默认
print("\n--- ① 默认配置 ---")
default_logger = logging.getLogger("demo.default")
default_logger.warning("发送欢迎通知给 张三")

# ------------------------------------------------------------------ ② 自定义格式
print("\n--- ② 自定义格式 ---")


def build_logger(name: str, fmt: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(fmt))
        logger.addHandler(handler)
    return logger


simple = build_logger(
    "demo.simple",
    "%(asctime)s %(levelname)-7s %(name)s: %(message)s",
)
simple.info("发送欢迎通知给 张三")
simple.warning("慢请求 GET /users 320.5ms")

# ------------------------------------------------------------------ ③ 请求 id
print("\n--- ③ 加上请求 id ---")

# contextvar: 每个协程/请求各有一份, 不会互相串
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    """把 contextvar 里的 request_id 塞进每条日志."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


trace_logger = logging.getLogger("demo.trace")
trace_logger.setLevel(logging.INFO)
trace_logger.propagate = False
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)-7s [%(request_id)s] %(name)s: %(message)s")
)
handler.addFilter(RequestIdFilter())
trace_logger.addHandler(handler)

trace_logger.info("没有请求上下文时, request_id 是默认值")

token = request_id_ctx.set("a1b2c3d4e5f6")
try:
    trace_logger.info("在请求里, request_id 自动带上")
    trace_logger.warning("这条慢请求日志也能串起来了")
finally:
    request_id_ctx.reset(token)

trace_logger.info("退出请求后, 又回到默认值")

print("\n--- 结论 ---")
print("    光有日志不够, 要能回答三个问题:")
print("      什么时候发生的  -> 时间戳")
print("      是哪个请求的    -> request_id")
print("      哪个模块打的    -> logger 名字")
