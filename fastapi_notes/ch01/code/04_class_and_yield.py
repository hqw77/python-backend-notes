"""FastAPI 第二部分 - 案例 4: 类作为依赖 + yield 的清理时机.

两个进阶用法:
    1. 类作为依赖: 把一组相关参数打包成一个对象, 用 __init__ 接收
    2. yield 依赖: 前半段准备资源, yield 之后做清理(即使抛异常也会执行)

怎么跑:
    python fastapi_notes/ch01/code/04_class_and_yield.py
"""

import warnings

warnings.filterwarnings("ignore")

from fastapi import Depends, FastAPI, Query  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()

log: list[str] = []


# ------------------------------------------------ 类依赖
class Pagination:
    """把 page / size / offset 打包成一个对象.

    FastAPI 会把 __init__ 的参数当成查询参数解析.
    """

    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(10, ge=1, le=100, description="每页条数"),
    ) -> None:
        self.page = page
        self.size = size
        self.offset = (page - 1) * size


@app.get("/items")
def list_items(p: Pagination = Depends()):
    """Depends() 不写参数时, 类型注解就是依赖本身."""
    return {"page": p.page, "size": p.size, "offset": p.offset}


# ------------------------------------------------ yield 依赖
class FakeSession:
    """模拟数据库会话: 进入时打开, 退出时关闭."""

    def __init__(self) -> None:
        self.opened = True
        log.append("打开连接")

    def close(self) -> None:
        self.opened = False
        log.append("关闭连接")


def get_session():
    """yield 依赖: yield 之前是准备, 之后是清理."""
    session = FakeSession()
    try:
        yield session
    finally:
        session.close()


@app.get("/with-session")
def with_session(session: FakeSession = Depends(get_session)):
    log.append("执行路由函数")
    return {"连接是否打开": session.opened}


@app.get("/boom")
def boom(session: FakeSession = Depends(get_session)):
    """路由里抛异常, 清理代码依然会执行."""
    log.append("路由抛异常")
    raise ValueError("故意报错")


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 类依赖: 一组参数变成一个对象")
        print("    GET /items                 ->", client.get("/items").json())
        print("    GET /items?page=3&size=20  ->", client.get("/items?page=3&size=20").json())

        show("② 类依赖也继承了 Query 的校验")
        r = client.get("/items?size=999")
        print("    GET /items?size=999        ->", r.status_code, r.json()["detail"][0]["msg"])

        show("③ yield 依赖: 正常请求的执行顺序")
        log.clear()
        r = client.get("/with-session")
        print("    返回:", r.json())
        print("    执行顺序:", " -> ".join(log))

        show("④ 路由抛异常时, yield 后面的清理照样执行")
        log.clear()
        try:
            client.get("/boom")
        except ValueError:
            pass
        print("    执行顺序:", " -> ".join(log))
        print("    → 关闭连接这一步没有被跳过")

        show("⑤ 为什么项目里要用 yield 管 Session")
        print("    请求正常返回 -> 关 Session")
        print("    请求抛异常   -> 关 Session")
        print("    连接一定归还连接池, 不会泄漏")
