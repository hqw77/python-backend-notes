"""FastAPI 第二部分 - 案例 1: 在 async def 里写阻塞调用会怎样.

FastAPI 是异步框架, 所有 async def 的路由都在同一个事件循环里跑.
如果里面写了同步阻塞的代码(time.sleep / requests / 同步查库),
整个事件循环会被卡住, 其他请求只能排队.

这个案例用 5 个并发请求 + 每请求 0.3 秒, 对比"阻塞"和"不阻塞"的总耗时.

怎么跑:
    python fastapi_notes/ch03/code/01_blocking_event_loop.py
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


@app.get("/blocking")
async def blocking():
    """async def 里用了同步阻塞的 time.sleep."""
    time.sleep(SLEEP)
    return {"ok": True}


@app.get("/non-blocking")
async def non_blocking():
    """async def 里用 await asyncio.sleep, 会主动让出控制权."""
    await asyncio.sleep(SLEEP)
    return {"ok": True}


async def measure(path: str) -> float:
    """并发发 N 个请求, 返回总耗时."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        start = time.perf_counter()
        await asyncio.gather(*[client.get(path) for _ in range(N)])
        return time.perf_counter() - start


async def main() -> None:
    print(f"\n并发 {N} 个请求, 每个 sleep {SLEEP} 秒\n")

    print("--- ① async def + time.sleep(阻塞) ---")
    cost = await measure("/blocking")
    print(f"    总耗时: {cost:.2f} 秒")
    print(f"    理论值: {N * SLEEP:.2f} 秒 (5 个请求完全串行)")
    print("    → 事件循环被卡住, 请求只能排队, 一个接一个执行")

    print("\n--- ② async def + await asyncio.sleep(非阻塞) ---")
    cost = await measure("/non-blocking")
    print(f"    总耗时: {cost:.2f} 秒")
    print(f"    理论值: {SLEEP:.2f} 秒 (5 个请求真正并发)")
    print("    → await 把控制权交回事件循环, 其他请求可以插进来")

    print("\n--- 结论 ---")
    print("    在 async def 里写同步阻塞代码, 等于把异步框架用成了单线程串行.")
    print("    表现为: 并发一高, 所有接口一起变慢, CPU 却不高.")


if __name__ == "__main__":
    asyncio.run(main())
