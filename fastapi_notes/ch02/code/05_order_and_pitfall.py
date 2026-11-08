"""FastAPI 第二部分 - 案例 5: 中间件的顺序, 以及一个容易踩的坑.

两个知识点:
    1. 多个中间件是"洋葱式"嵌套: 后加的在外面, 先进入, 后返回
    2. 中间件里抛的异常, 不会被 @app.exception_handler 捕获

怎么跑:
    python fastapi_notes/ch02/code/05_order_and_pitfall.py
"""

import sys
import warnings
from pathlib import Path

# 这个案例要复用 project/ 里的业务异常, 所以先把工程目录加进 sys.path
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project"))
warnings.filterwarnings("ignore")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.exceptions import AppError, NotFoundError  # noqa: E402

app = FastAPI()

log: list[str] = []


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """这个处理器只负责"路由/依赖里抛出的 AppError"."""
    log.append(f"异常处理器接住: {exc.message}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


# ---------------------------------------------------------------- 中间件
@app.middleware("http")
async def middleware_a(request: Request, call_next):
    log.append("A 进入")
    response = await call_next(request)
    log.append("A 返回")
    return response


@app.middleware("http")
async def middleware_b(request: Request, call_next):
    log.append("B 进入")
    response = await call_next(request)
    log.append("B 返回")
    return response


@app.middleware("http")
async def boom_middleware(request: Request, call_next):
    """专门用来演示"中间件抛异常"的情况."""
    if request.url.path == "/mw-boom":
        raise ValueError("中间件里报错")
    return await call_next(request)


# ---------------------------------------------------------------- 路由
@app.get("/hello")
def hello():
    log.append("路由函数")
    return {"msg": "hi"}


@app.get("/app-error")
def app_error():
    log.append("路由抛 AppError")
    raise NotFoundError("用户不存在")


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 三个中间件的执行顺序(洋葱模型)")
        log.clear()
        r = client.get("/hello")
        print("    返回:", r.json())
        for i, item in enumerate(log, 1):
            print(f"      {i}. {item}")
        print("    → 注册顺序是 A, B, boom, 执行顺序是 boom -> B -> A")
        print("      后注册的在更外层, 所以 B 比 A 先进入")
        print("    → 返回时反过来(洋葱从里往外剥): A 返回 -> B 返回 -> boom 返回")

        show("② 路由抛 AppError: 被 exception_handler 接住 -> 404")
        log.clear()
        r = client.get("/app-error")
        print("    状态码:", r.status_code, " 响应:", r.json())
        for item in log:
            print("      " + item)

        show("③ 中间件抛异常: 不会被 exception_handler 接住")
        broken = TestClient(app, raise_server_exceptions=False)
        log.clear()
        r = broken.get("/mw-boom")
        print("    状态码:", r.status_code, "(变成 500 了)")
        print("    执行记录:")
        for item in log:
            print("      " + item)
        print("    → 日志里没有'异常处理器接住', 说明它根本没被调用")

        show("④ 为什么")
        print("    中间件在 exception_handler 的外面(更靠外)")
        print("    异常从中间件抛出时, 已经越过了异常处理层")
        print("    → 中间件里的代码要自己 try/except")

        show("⑤ 正确的中间件写法")
        print("    async def mw(request, call_next):")
        print("        try:")
        print("            return await call_next(request)")
        print("        except Exception:")
        print("            # 这里兜底, 或者记日志后重新抛")
        print("            raise")
