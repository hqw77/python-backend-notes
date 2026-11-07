"""FastAPI 第二部分 - 案例 1: 依赖注入是什么.

Depends 的作用: 把一个"准备数据"的函数挂到路由参数上,
FastAPI 会在调用路由函数之前先执行它, 把返回值塞进参数.

顺带的好处: 依赖函数里的参数(page, size 等)会自动变成查询参数,
不用在路由里重复声明.

怎么跑:
    python fastapi_notes/ch01/code/01_depends_basic.py
"""

import warnings

warnings.filterwarnings("ignore")

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()


def pagination(page: int = 1, size: int = 10) -> dict:
    """依赖函数: 接收两个查询参数, 返回一个字典."""
    return {"page": page, "size": size, "offset": (page - 1) * size}


def current_user(token: str = "anonymous") -> str:
    """依赖函数: 模拟从 token 解析出用户名."""
    return f"user-{token}"


@app.get("/items/plain")
def list_plain():
    """没有依赖: 分页参数得自己声明, 每个接口重复写一遍."""
    return {"msg": "这个接口没法分页, 因为参数没声明"}


@app.get("/items")
def list_items(p: dict = Depends(pagination)):
    """用了依赖: 分页参数由依赖管, 路由只关心业务."""
    return {"分页参数": p}


@app.get("/me")
def me(who: str = Depends(current_user)):
    """依赖也可以只提供一个值."""
    return {"当前用户": who}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 用依赖的分页接口: 默认值")
        print("    GET /items          ->", client.get("/items").json())

        show("② 依赖函数的参数会自动变成查询参数")
        print("    GET /items?page=2&size=5 ->", client.get("/items?page=2&size=5").json())

        show("③ 参数类型不对时, 由依赖负责校验")
        r = client.get("/items?page=abc")
        print("    GET /items?page=abc ->", r.status_code)
        print("    错误:", r.json()["detail"][0]["msg"])

        show("④ 依赖只提供一个值也行")
        print("    GET /me?token=42    ->", client.get("/me?token=42").json())

        show("⑤ 打开文档会看到什么")
        schema = client.get("/openapi.json").json()
        params = schema["paths"]["/items"]["get"]["parameters"]
        print("    /items 的查询参数:", [p["name"] for p in params])
        print("    → 依赖里的参数自动出现在接口文档里, 不用手写")
