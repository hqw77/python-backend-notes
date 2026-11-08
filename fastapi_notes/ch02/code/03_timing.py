"""FastAPI 第二部分 - 案例 3: 耗时统计与慢请求告警.

做法: 在中间件里记开始时间, 响应返回后算差值, 超过阈值就打警告.

为什么用 perf_counter 而不是 time.time:
    time.time() 受系统时钟调整影响(比如 NTP 校准), 可能算出负数.
    time.perf_counter() 是单调递增的, 专门用来测耗时.

怎么跑:
    python fastapi_notes/ch02/code/03_timing.py
"""

import time
import warnings

warnings.filterwarnings("ignore")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()

SLOW_THRESHOLD_MS = 100        # 超过 100ms 算慢请求

slow_requests: list[str] = []


@app.middleware("http")
async def add_timing(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    cost_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time"] = f"{cost_ms:.1f}ms"

    if cost_ms > SLOW_THRESHOLD_MS:
        slow_requests.append(f"{request.method} {request.url.path} {cost_ms:.1f}ms")

    return response


@app.get("/fast")
def fast():
    return {"msg": "很快"}


@app.get("/slow")
def slow():
    time.sleep(0.3)             # 模拟慢查询
    return {"msg": "很慢"}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 快速接口: 响应头带耗时")
        r = client.get("/fast")
        print("    X-Process-Time ->", r.headers["X-Process-Time"])
        print("    慢请求记录数   ->", len(slow_requests))

        show("② 慢接口: 会被记进慢请求清单")
        r = client.get("/slow")
        print("    X-Process-Time ->", r.headers["X-Process-Time"])
        print("    慢请求记录数   ->", len(slow_requests))
        print("    记录内容       ->", slow_requests)

        show("③ 阈值在这里起作用")
        print("    SLOW_THRESHOLD_MS =", SLOW_THRESHOLD_MS)
        print("    快速接口:", "< 阈值, 不记录")
        print("    慢接口  :", "> 阈值, 记录一条")

        show("④ 生产环境怎么用")
        print("    把 slow_requests 换成打日志/上报监控")
        print("    告警规则: 5 分钟内慢请求超过 N 条就报警")
        print("    常见阈值: 接口 200ms, 数据库 50ms")

        show("⑤ 为什么不用 time.time()")
        print("    time.time() 会被系统时钟校准影响, 可能算出负数")
        print("    time.perf_counter() 单调递增, 只用来测间隔")
