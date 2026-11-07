"""Redis 第三章 - 案例 2: 写操作怎么让缓存失效.

顺序必须是:
    先改数据库 -> 再删缓存
反过来的话, 读线程可能在两步之间把旧值写回缓存, 见第二章 2.8.

这个案例调真实接口: 先查一次(写缓存) -> 改余额 -> 观察缓存消失 -> 再查(重建).

怎么跑:
    python redis_notes/ch03/code/02_invalidation.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project"))
warnings.filterwarnings("ignore")

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import cache  # noqa: E402

KEY = "user:2"


def show(title: str) -> None:
    print(f"\n--- {title} ---")


def state(tag: str) -> None:
    print(f"    {tag:16} 缓存存在: {cache.exists(KEY)}, 剩余 {cache.ttl(KEY)} 秒")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 先清缓存")
        cache.delete(KEY)
        state("清理后")

        show("② 查一次详情: 未命中 -> 查库 -> 回写缓存")
        r = client.get("/users/2")
        original_balance = r.json()["balance"]      # 记下原始值, 结束时还原
        print("    余额:", original_balance)
        state("查完之后")

        show("③ 再查一次: 直接命中缓存, 不再查库")
        r = client.get("/users/2")
        print("    余额:", r.json()["balance"])
        state("再查之后")

        show("④ 改余额: 先改库, 再删缓存")
        r = client.put("/users/2/balance", json={"amount": "1.00"})
        print("    改完余额:", r.json()["balance"])
        state("改完之后")

        show("⑤ 再查: 缓存被删了, 重新查库并回写")
        r = client.get("/users/2")
        print("    余额:", r.json()["balance"], "(已经是最新值)")
        state("重建之后")

        show("⑥ 软删除也会让缓存失效")
        cache.delete(KEY)
        client.get("/users/2")
        state("删除前")
        client.delete("/users/2")
        state("软删后")

        show("⑦ 恢复数据并清理缓存")
        # 把余额和 is_deleted 都改回原样, 免得影响其他案例
        import pymysql

        from app.core.config import settings

        conn = pymysql.connect(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            database=settings.mysql_database,
            charset="utf8mb4",
        )
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET is_deleted = 0, balance = %s WHERE id = 2",
                    (original_balance,),
                )
            conn.commit()
        finally:
            conn.close()
        cache.delete(KEY)
        print(f"    已恢复 id=2 的余额为 {original_balance}, 并清理缓存")
