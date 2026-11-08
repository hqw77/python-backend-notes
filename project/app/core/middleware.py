"""全局中间件: 请求 id 与耗时统计.

一个中间件同时做两件事, 因为它们都需要"包住整个请求":
    1. 生成或复用 X-Request-ID, 写进 request.state 和响应头
    2. 记录处理耗时, 超过阈值打慢请求日志

为什么放在一个中间件里:
    两件事都要在 await call_next(request) 前后各执行一段,
    拆成两个中间件也能做, 但会多一层嵌套, 排查顺序问题时更绕.
"""

import logging
import time
import uuid

from fastapi import FastAPI, Request

logger = logging.getLogger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"
PROCESS_TIME_HEADER = "X-Process-Time"
SLOW_THRESHOLD_MS = 200      # 超过这个耗时就打警告日志


def register_middlewares(app: FastAPI) -> None:
    """把项目的中间件挂到应用上. 在 main.py 里调用一次."""

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        # ---- 请求阶段 ----
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex[:12]
        request.state.request_id = request_id
        start = time.perf_counter()

        # ---- 交给路由 ----
        response = await call_next(request)

        # ---- 响应阶段 ----
        cost_ms = (time.perf_counter() - start) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id
        response.headers[PROCESS_TIME_HEADER] = f"{cost_ms:.1f}ms"

        if cost_ms > SLOW_THRESHOLD_MS:
            logger.warning(
                "慢请求 %s %s %.1fms request_id=%s",
                request.method,
                request.url.path,
                cost_ms,
                request_id,
            )

        return response
