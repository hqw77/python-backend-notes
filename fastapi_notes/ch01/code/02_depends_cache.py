"""FastAPI 第二部分 - 案例 2: 依赖的缓存机制.

同一个请求里, 如果两个参数依赖同一个函数, FastAPI 只会执行一次,
把返回值复用给两边. 这叫 "依赖缓存" (use_cache=True, 默认开启).

为什么重要: 如果依赖是"查当前用户"(每次要查一次库),
一个请求里用到三次, 不加缓存就要查三次库.

怎么跑:
    python fastapi_notes/ch01/code/02_depends_cache.py
"""

import warnings

warnings.filterwarnings("ignore")

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()

# 记录依赖被真正执行了几次
calls = {"n": 0}


def expensive_dep() -> dict:
    """模拟"每次执行都很贵"的依赖, 比如查一次数据库."""
    calls["n"] += 1
    return {"value": "查了一次库", "calls": calls["n"]}


@app.get("/cached")
def use_twice(
    a: dict = Depends(expensive_dep),
    b: dict = Depends(expensive_dep),
):
    """两个参数依赖同一个函数."""
    return {"a": a, "b": b, "依赖执行次数": calls["n"]}


@app.get("/no-cache")
def use_twice_nocache(
    a: dict = Depends(expensive_dep, use_cache=False),
    b: dict = Depends(expensive_dep, use_cache=False),
):
    """关掉缓存: 每处各执行一次."""
    return {"a": a, "b": b, "依赖执行次数": calls["n"]}


@app.get("/different-params")
def different_params(
    a: dict = Depends(expensive_dep),
    b: dict = Depends(expensive_dep),
    c: dict = Depends(expensive_dep),
):
    """同一个请求里用三次."""
    return {"执行次数": calls["n"]}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 默认开启缓存: 一个请求里用两次, 只执行一次")
        calls["n"] = 0
        r = client.get("/cached")
        print("    返回:", r.json())
        print("    → a 和 b 是同一个对象, 依赖只跑了 1 次")

        show("② 用三次也只执行一次")
        calls["n"] = 0
        r = client.get("/different-params")
        print("    返回:", r.json())

        show("③ 关掉缓存: 每处各执行一次")
        calls["n"] = 0
        r = client.get("/no-cache")
        print("    返回:", r.json())
        print("    → use_cache=False 时, 两个参数各跑一次")

        show("④ 缓存的作用范围: 只在同一个请求内")
        calls["n"] = 0
        client.get("/cached")
        client.get("/cached")
        print("    连续请求两次, 依赖总执行次数:", calls["n"])
        print("    → 每个请求重新开始计数, 不会跨请求缓存")

        show("⑤ 什么时候该关掉缓存")
        print("    依赖有副作用(写库, 发消息)")
        print("    依赖每次需要拿到最新值, 不能复用")
        print("    其他情况保持默认即可")
