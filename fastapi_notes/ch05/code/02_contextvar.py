"""FastAPI 第二部分 - 案例 5-2: 为什么用 contextvar 而不是全局变量.

并发场景下, 每个请求的 request_id 必须互不干扰.
用全局变量会串号, 用 contextvar 不会.

这个案例用 asyncio 并发跑三个"请求", 对比两种做法.

怎么跑:
    python fastapi_notes/ch05/code/02_contextvar.py
"""

import asyncio
from contextvars import ContextVar

# ------------------------------------------------------------------ 全局变量
GLOBAL_ID = {"value": "-"}


async def handle_with_global(name: str, delay: float) -> str:
    GLOBAL_ID["value"] = name              # 先写
    await asyncio.sleep(delay)             # 等一会儿(模拟查库)
    return f"{name} 读到的 id = {GLOBAL_ID['value']}"   # 再读


# ------------------------------------------------------------------ contextvar
current_id: ContextVar[str] = ContextVar("current_id", default="-")


async def handle_with_contextvar(name: str, delay: float) -> str:
    current_id.set(name)
    await asyncio.sleep(delay)
    return f"{name} 读到的 id = {current_id.get()}"


async def main() -> None:
    print("\n--- ① 用全局变量(会串号) ---")
    results = await asyncio.gather(
        handle_with_global("req-A", 0.3),
        handle_with_global("req-B", 0.2),
        handle_with_global("req-C", 0.1),
    )
    for line in results:
        print("    " + line)
    print("    → 三个请求读到的都是'最后一个写的', 全串了")

    print("\n--- ② 用 contextvar(互不干扰) ---")
    results = await asyncio.gather(
        handle_with_contextvar("req-A", 0.3),
        handle_with_contextvar("req-B", 0.2),
        handle_with_contextvar("req-C", 0.1),
    )
    for line in results:
        print("    " + line)
    print("    → 每个协程有自己的那份, 不会被别的请求改掉")

    print("\n--- ③ 为什么 ---")
    print("    全局变量全进程只有一份, 谁最后写就是谁")
    print("    contextvar 跟着'当前执行上下文'走, asyncio 每个 task 一份")
    print("    → 所以在中间件里 set, 在 service / 日志里 get, 拿到的一定是自己的")


if __name__ == "__main__":
    asyncio.run(main())
