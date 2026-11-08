"""FastAPI 第二部分 - 案例 2: 请求 id 透传.

为什么需要请求 id:
    线上出问题时, 一个请求会打很多条日志(网关/应用/数据库).
    没有统一 id 就没法把它们串起来.

做法:
    1. 客户端带了 X-Request-ID 就用它, 没带就自己生成一个
    2. 存进 request.state 供后续使用
    3. 响应头里带回去, 方便用户报障时提供

怎么跑:
    python fastapi_notes/ch02/code/02_request_id.py
"""

import uuid
import warnings

warnings.filterwarnings("ignore")

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()

HEADER = "X-Request-ID"


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    # 客户端可能已经带了一个(比如网关生成的), 优先复用
    request_id = request.headers.get(HEADER) or uuid.uuid4().hex[:12]

    # 存到 request.state, 路由函数里可以直接取
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers[HEADER] = request_id
    return response


@app.get("/hello")
def hello(request: Request):
    return {"msg": "hi", "你的请求 id": request.state.request_id}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 客户端没带 id: 服务端自己生成")
        r = client.get("/hello")
        print("    响应头 X-Request-ID ->", r.headers.get(HEADER))
        print("    响应体里的 id       ->", r.json()["你的请求 id"])
        print("    → 两处一致, 说明是同一个值透传下来的")

        show("② 客户端带了 id: 复用客户端的")
        r = client.get("/hello", headers={HEADER: "client-abc-123"})
        print("    响应头 X-Request-ID ->", r.headers.get(HEADER))
        print("    响应体里的 id       ->", r.json()["你的请求 id"])

        show("③ 两次请求的 id 不一样")
        a = client.get("/hello").headers[HEADER]
        b = client.get("/hello").headers[HEADER]
        print("    第一次:", a)
        print("    第二次:", b)
        print("    相同吗:", a == b, "(应该不同)")

        show("④ 为什么用 uuid4().hex[:12] 而不是完整 uuid")
        print("    完整 uuid 是 36 字符, 日志里太长")
        print("    12 位十六进制 = 16^12 种可能, 对单机日志足够区分")
        print("    要全局唯一就用完整 uuid")
