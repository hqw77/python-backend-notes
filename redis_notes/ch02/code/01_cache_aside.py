"""Redis 第二章 - 案例 1: Cache-Aside 的完整读写路径.

Cache-Aside(旁路缓存)是最常用的缓存写法:
    读: 先查缓存 -> 没有就查数据库 -> 把结果写回缓存
    写: 先改数据库 -> 再删缓存

怎么跑:
    python redis_notes/ch02/code/01_cache_aside.py

这里用一个"查一次要 50 毫秒"的假数据库, 模拟真实 MySQL 的慢查询,
这样能明显看出缓存省了多少时间.
"""

import json
import time

import redis

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)


class FakeDB:
    """假数据库: 每次查询睡 50ms, 并记录被查了多少次."""

    def __init__(self) -> None:
        self.rows = {
            1: {"id": 1, "username": "张三", "balance": "888.00"},
            2: {"id": 2, "username": "李四", "balance": "400.00"},
        }
        self.query_count = 0

    def get_user(self, user_id: int):
        self.query_count += 1
        time.sleep(0.05)                     # 模拟数据库往返
        return self.rows.get(user_id)

    def update_balance(self, user_id: int, balance: str) -> None:
        self.query_count += 1
        time.sleep(0.05)
        self.rows[user_id]["balance"] = balance


db = FakeDB()


def show(title: str) -> None:
    print(f"\n--- {title} ---")


def get_user_cached(user_id: int):
    """Cache-Aside 的读路径."""
    key = f"user:{user_id}"

    cached = r.get(key)                      # 1. 先看缓存
    if cached is not None:
        return json.loads(cached)            #    命中, 直接返回

    user = db.get_user(user_id)              # 2. 没命中, 查数据库
    if user is None:
        return None

    r.set(key, json.dumps(user, ensure_ascii=False), ex=300)   # 3. 写回缓存, 5 分钟过期
    return user


def update_balance(user_id: int, balance: str) -> None:
    """Cache-Aside 的写路径: 先改库, 再删缓存."""
    db.update_balance(user_id, balance)
    r.delete(f"user:{user_id}")
    print(f"    改库完成, 已删除缓存 user:{user_id}")


if __name__ == "__main__":
    for key in ("user:1", "user:2"):
        r.delete(key)

    show("① 第一次读: 缓存是空的, 只能查数据库")
    before = db.query_count
    print("    结果             ->", get_user_cached(1))
    print("    数据库被查       ->", db.query_count - before, "次")

    show("② 第二次读: 直接命中缓存")
    before = db.query_count
    print("    结果             ->", get_user_cached(1))
    print("    数据库被查       ->", db.query_count - before, "次 (没有增长)")

    show("③ 连续读 100 次: 数据库一次都没被打")
    before = db.query_count
    start = time.perf_counter()
    for _ in range(100):
        get_user_cached(1)
    cost = (time.perf_counter() - start) * 1000
    print("    数据库被查       ->", db.query_count - before, "次")
    print(f"    100 次总耗时     -> {cost:.1f} ms, 平均 {cost / 100:.2f} ms/次")

    show("④ 写操作: 改库 + 删缓存")
    update_balance(1, "588.00")
    print("    缓存还在吗       ->", r.exists("user:1"), "(0 表示已经删掉)")

    show("⑤ 写之后再读: 会重新加载最新的值")
    before = db.query_count
    print("    结果             ->", get_user_cached(1))
    print("    数据库被查       ->", db.query_count - before, "次 (重建了一次)")

    show("⑥ 对比: 完全不使用缓存")
    before = db.query_count
    start = time.perf_counter()
    for _ in range(100):
        db.get_user(1)
    cost = (time.perf_counter() - start) * 1000
    print("    数据库被查       ->", db.query_count - before, "次")
    print(f"    100 次总耗时     -> {cost:.1f} ms, 平均 {cost / 100:.2f} ms/次")

    show("⑦ 清理")
    for key in ("user:1", "user:2"):
        r.delete(key)
    print("    已清理")
