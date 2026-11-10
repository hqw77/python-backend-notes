"""FastAPI 第二部分 - 案例 2: 普通 def 为什么不会卡住.

FastAPI 对两种函数的处理不一样:
    async def -> 直接在事件循环里跑
    普通 def  -> 丢到线程池里跑(默认 40 个线程)

所以"同步阻塞的代码"写成普通 def 反而没事, 写成 async def 才会卡死.

这个案例用同一个阻塞函数, 分别用 async def 和 def 包装, 对比并发耗时.

怎么跑:
    python fastapi_notes/ch03/code/02_def_in_threadpool.py
"""

import asyncio
import time
import warnings

warnings.filterwarnings("ignore")

import httpx  # noqa: E402
from fastapi import FastAPI  # noqa: E402

SLEEP = 0.3
N = 5

app = FastAPI()


def blocking_work() -> str:
    """一个同步阻塞函数, 比如 requests.get / 同步查库."""
    time.sleep(SLEEP)
    return "done"


@app.get("/async-def")
async def async_def():
    """用 async def 包同步函数 -> 卡住事件循环."""
    return {"result": blocking_work()}


@app.get("/plain-def")
def plain_def():
    """用普通 def 包同步函数 -> FastAPI 丢到线程池, 不卡事件循环."""
    return {"result": blocking_work()}


async def measure(path: str) -> float:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.perf_counter()
        await asyncio.gather(*[client.get(path) for _ in range(N)])
        return time.perf_counter() - start


async def main() -> None:
    print(f"\n并发 {N} 个请求, 每个耗时 {SLEEP} 秒\n")

    print("--- ① async def 包同步阻塞函数 ---")
    cost = await measure("/async-def")
    print(f"    总耗时: {cost:.2f} 秒")
    print(f"    → 串行执行, 等于 {N} 次 {SLEEP} 秒")

    print("\n--- ② 普通 def 包同一个函数 ---")
    cost = await measure("/plain-def")
    print(f"    总耗时: {cost:.2f} 秒")
    print(f"    → 线程池并发, 接近 {SLEEP} 秒")

    print("\n--- 结论 ---")
    print("    同步代码 -> 用普通 def, FastAPI 自动丢线程池")
    print("    异步代码 -> 用 async def + await")
    print("    最糟的组合: async def + 同步阻塞调用")


if __name__ == "__main__":
    asyncio.run(main())
