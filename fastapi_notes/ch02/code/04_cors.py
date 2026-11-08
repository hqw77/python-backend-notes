"""FastAPI 第二部分 - 案例 4: CORS 到底是什么.

浏览器有个安全规则叫"同源策略":
    页面在 http://localhost:3000, 用 fetch 请求 http://127.0.0.1:8000
    端口不同 -> 不同源 -> 浏览器默认不允许

CORS(跨域资源共享) 就是服务端告诉浏览器: "我允许这个来源访问我".
注意: 这是浏览器在拦, 用 curl / Postman 调接口不受影响.

怎么跑:
    python fastapi_notes/ch02/code/04_cors.py
"""

import warnings

warnings.filterwarnings("ignore")

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


def build_app(with_cors: bool) -> FastAPI:
    app = FastAPI()

    if with_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],   # 允许的前端地址
            allow_methods=["*"],                        # 允许的方法
            allow_headers=["*"],                        # 允许的请求头
            allow_credentials=True,                     # 允许带 cookie
            max_age=600,                                # 预检结果缓存 10 分钟
        )

    @app.get("/hello")
    def hello():
        return {"msg": "hi"}

    return app


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    preflight = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }

    show("① 不加 CORS: 浏览器会拦下(接口本身没拒绝, 是浏览器不让看)")
    with TestClient(build_app(False)) as client:
        r = client.options("/hello", headers=preflight)
        print("    预检 OPTIONS 状态码 ->", r.status_code)
        print("    Access-Control-Allow-Origin ->", r.headers.get("access-control-allow-origin"))

    show("② 加了 CORS: 预检通过, 浏览器放行")
    with TestClient(build_app(True)) as client:
        r = client.options("/hello", headers=preflight)
        print("    预检 OPTIONS 状态码 ->", r.status_code)
        print("    Access-Control-Allow-Origin  ->", r.headers.get("access-control-allow-origin"))
        print("    Access-Control-Allow-Methods ->", r.headers.get("access-control-allow-methods"))
        print("    Access-Control-Max-Age       ->", r.headers.get("access-control-max-age"))

    show("③ 实际请求也会带上允许来源的头")
    with TestClient(build_app(True)) as client:
        r = client.get("/hello", headers={"Origin": "http://localhost:3000"})
        print("    状态码 ->", r.status_code)
        print("    Access-Control-Allow-Origin ->", r.headers.get("access-control-allow-origin"))

    show("④ 不在白名单的来源会被拒绝")
    with TestClient(build_app(True)) as client:
        r = client.get("/hello", headers={"Origin": "http://evil.com"})
        print("    状态码 ->", r.status_code, "(接口本身还是 200)")
        print("    Access-Control-Allow-Origin ->", r.headers.get("access-control-allow-origin"))
        print("    → 没有这个头, 浏览器就会拦住响应, 前端拿不到数据")

    show("⑤ 什么时候需要 CORS")
    print("    前后端分开部署(前端 3000, 后端 8000)  -> 需要")
    print("    同域名不同端口                        -> 需要")
    print("    用 Nginx 把前后端放同一个域名         -> 不需要")
    print("    服务端调服务端(curl / 内部调用)       -> 浏览器规则不适用")
