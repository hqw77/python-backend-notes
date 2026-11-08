"""FastAPI 第二部分 - 案例 1: 中间件是什么, 执行顺序长什么样.

中间件是一段"包住"所有请求的代码:
    请求进来 -> 中间件前半段 -> 路由函数 -> 中间件后半段 -> 响应返回

它能看到每一个请求, 所以适合做: 记录请求 id, 统计耗时, 加响应头, 打日志.

怎么跑:
    python fastapi_notes/ch02/code/01_middleware_basic.py
"""

import warnings

warnings.filterwarnings("ignore")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()

log: list[str] = []


@app.middleware("http")
async def record(request: Request, call_next):
    """call_next 就是"把请求交给下一层", 返回值是 Response."""
    log.append(f"中间件 进入  {request.method} {request.url.path}")
    response = await call_next(request)
    log.append(f"中间件 返回  status={response.status_code}")
    return response


@app.get("/hello")
def hello():
    log.append("路由函数执行")
    return {"msg": "hi"}


@app.get("/boom")
def boom():
    log.append("路由函数抛异常")
    raise ValueError("故意报错")


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 正常请求: 中间件包住路由")
        log.clear()
        r = client.get("/hello")
        print("    返回:", r.json())
        print("    执行顺序:")
        for i, item in enumerate(log, 1):
            print(f"      {i}. {item}")

        show("② 中间件的执行是在路由之前和之后各一次")
        print("    await call_next(request) 这一句就是分界线:")
        print("    它之前 = 请求阶段, 它之后 = 响应阶段")

        show("③ 路由抛异常时, 中间件的后半段不会执行")
        log.clear()
        try:
            client.get("/boom")
        except ValueError:
            pass
        print("    执行顺序:")
        for i, item in enumerate(log, 1):
            print(f"      {i}. {item}")
        print("    → 没有 '中间件 返回', 因为异常直接往上冒了")

        show("④ 中间件能拿到什么")
        print("    request.method       ->", "GET")
        print("    request.url.path     -> /hello")
        print("    request.headers      -> 请求头")
        print("    request.state        -> 一个空对象, 可以用来传数据")
        print("    response.status_code ->", 200)
        print("    response.headers     -> 可以往这里加响应头")

        show("⑤ 中间件和 Depends 的区别")
        print("    中间件: 所有请求都经过, 拿不到路由参数, 适合横切关注点")
        print("    依赖  : 只对声明了它的接口生效, 能拿参数, 适合业务前置条件")
