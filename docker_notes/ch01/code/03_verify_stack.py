"""Docker 第一章 - 案例 3: 验证整套 compose 服务.

这个脚本做的是"接手一个新项目时最先做的事":
    看容器是否健康 -> 看应用日志 -> 打健康检查 -> 走一遍业务主流程

前提: 先在 project/ 目录执行过
    docker compose up -d --build

怎么跑:
    python docker_notes/ch01/code/03_verify_stack.py
"""

import json
import subprocess
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"


def sh(*args: str) -> str:
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return (result.stdout or result.stderr).strip()


def http(method: str, path: str, body: dict | None = None, token: str | None = None):
    """发一个 HTTP 请求, 返回 (状态码, 响应体)."""
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode()


def show(title: str) -> None:
    print(f"\n--- {title} ---")


def docker_ok() -> bool:
    """先探一下 docker 能不能用, 不能用就给一句人话提示."""
    result = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode == 0 and result.stdout.strip():
        return True
    print("    !! 连不上 Docker daemon")
    print("       常见原因: Docker Desktop 没启动, 或当前终端没有权限访问 docker 的命名管道")
    print("       处理: 打开 Docker Desktop 等它变绿; 仍失败就换一个普通终端重跑")
    return False


if __name__ == "__main__":
    has_docker = docker_ok()

    show("① 三个容器的健康状态")
    print(sh("docker", "ps", "--format", "{{.Names}}\t{{.Status}}") if has_docker else "    (跳过: 当前环境连不上 docker)")

    show("② 应用日志的最后几行(能看到迁移记录)")
    print(sh("docker", "compose", "-f", "project/docker-compose.yml", "logs", "app", "--tail", "4") if has_docker else "    (跳过)")

    show("③ 健康检查")
    print("    /health    ->", http("GET", "/health"))
    print("    /health/db ->", http("GET", "/health/db"))

    show("④ 业务主流程: 注册 -> 登录 -> 带令牌访问")
    import time

    stamp = int(time.time()) % 10000
    username = f"verify{stamp}"
    print("    注册:", http("POST", "/auth/register",
                            {"username": username, "phone": f"1360000{stamp:04d}", "password": "secret123"})[0])

    status, body = http("POST", "/auth/login", {"username": username, "password": "secret123"})
    token = json.loads(body)["access_token"]
    print("    登录:", status, " 令牌前 20 位:", token[:20] + "...")

    status, body = http("GET", "/auth/me", token=token)
    print("    /auth/me:", status, json.loads(body)["username"])

    show("⑤ 缓存是否真的写进了 Redis 容器")
    print("    docker exec pbn-redis redis-cli keys 'user:*'")
    print("    ", (sh("docker", "exec", "pbn-redis", "redis-cli", "keys", "user:*") if has_docker else "(跳过)") or "(空)")

    show("⑥ 清理")
    print("    验证数据留在容器里无所谓: docker compose down -v 会连数据一起清掉")
