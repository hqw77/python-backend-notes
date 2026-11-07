"""Redis 第三章 - 案例 1: 项目里的详情接口, 加缓存前后各发几条 SQL.

这个案例直接跑真实的 FastAPI 应用(不启动服务器, 用 TestClient),
用 SQLAlchemy 的事件钩子统计每条请求到底发了几条 SELECT.

怎么跑:
    python redis_notes/ch03/code/01_cache_in_project.py

前提: MySQL 与 Redis 都在跑, project/.env 已配置.
"""

import sys
import warnings
from pathlib import Path

# 工程在仓库根的 project/ 下, 把它加入 sys.path 才能 import app
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project"))
warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import event  # noqa: E402

from app.db.engine import engine  # noqa: E402
from app.db.redis_client import redis_client  # noqa: E402
from app.main import app  # noqa: E402

# 每发一条 SQL 就记下来
sql_log: list[str] = []


@event.listens_for(engine, "before_cursor_execute")
def _record(conn, cursor, statement, parameters, context, executemany):
    sql_log.append(" ".join(statement.split()))


def take_sql() -> list[str]:
    """取出上次清空以来的 SELECT 语句."""
    rows = [s for s in sql_log if s.upper().startswith("SELECT")]
    sql_log.clear()
    return rows


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    key = "user:1"

    with TestClient(app) as client:
        show("① 先清掉缓存, 模拟'冷启动'")
        redis_client.delete(key)
        take_sql()
        print("    缓存存在:", redis_client.exists(key))

        show("② 连续请求详情接口 3 次, 每次都统计 SQL")
        for i in range(1, 4):
            r = client.get("/users/1")
            rows = take_sql()
            print(f"    第 {i} 次: 状态码 {r.status_code}, 用户名 {r.json()['username']}, 发了 {len(rows)} 条 SELECT")
            if rows:
                print(f"             SQL: {rows[0][:70]}...")

        show("③ 缓存的内容与剩余时间")
        print("    缓存 key :", key)
        print("    剩余秒数 :", redis_client.ttl(key))
        print("    缓存内容 :", redis_client.get(key)[:80], "...")

        show("④ 结论")
        print("    第 1 次: 缓存没有 -> 查库 -> 回写缓存   (1 条 SELECT)")
        print("    第 2, 3 次: 直接命中缓存              (0 条 SELECT)")
        print("    → 命中率越高, 数据库压力越小")

        show("⑤ 清理")
        redis_client.delete(key)
        print("    已清理")
