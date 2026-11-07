"""Redis 第二章 - 案例 2: 穿透, 击穿, 雪崩.

三个问题长得像, 但成因不同:
    穿透 = 查一个根本不存在的 id      -> 每次都绕过缓存直接打库
    击穿 = 一个热点 key 刚好过期      -> 并发请求同时打到库
    雪崩 = 一大批 key 同一时刻过期    -> 数据库瞬间被压垮

怎么跑:
    python redis_notes/ch02/code/02_three_problems.py
"""

import json
import random
import threading
import time

import redis

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)


class FakeDB:
    """假数据库, 记录被查了多少次."""

    def __init__(self) -> None:
        self.rows = {1: {"id": 1, "username": "张三"}}
        self.hits = 0
        self._lock = threading.Lock()

    def get_user(self, user_id: int):
        with self._lock:
            self.hits += 1
        time.sleep(0.05)                       # 模拟慢查询
        return self.rows.get(user_id)


db = FakeDB()


def show(title: str) -> None:
    print(f"\n--- {title} ---")


# ------------------------------------------------------------ 穿透
def read_plain(user_id: int):
    """不防护: 查不到就不缓存, 下次还查."""
    cached = r.get(f"plain:{user_id}")
    if cached is not None:
        return json.loads(cached)

    user = db.get_user(user_id)
    if user is not None:
        r.set(f"plain:{user_id}", json.dumps(user, ensure_ascii=False), ex=60)
    return user


def read_with_null(user_id: int):
    """防护: 查不到也缓存一个空标记, TTL 短一点."""
    key = f"null:{user_id}"
    cached = r.get(key)
    if cached is not None:
        return None if cached == "__NULL__" else json.loads(cached)

    user = db.get_user(user_id)
    if user is None:
        r.set(key, "__NULL__", ex=30)
        return None

    r.set(key, json.dumps(user, ensure_ascii=False), ex=300)
    return user


# ------------------------------------------------------------ 击穿
def read_no_lock(user_id: int):
    """没有锁: key 一过期, 并发全部打到库."""
    cached = r.get("hot")
    if cached is not None:
        return cached
    time.sleep(0.05)
    value = json.dumps(db.get_user(user_id), ensure_ascii=False)
    r.set("hot", value, ex=300)
    return value


def read_with_lock(user_id: int):
    """加互斥锁: 只让一个线程去查库."""
    cached = r.get("hot")
    if cached is not None:
        return cached

    got = r.set("hot:lock", "1", nx=True, ex=5)     # 只有抢到锁的才去查库
    if got:
        try:
            time.sleep(0.05)
            value = json.dumps(db.get_user(user_id), ensure_ascii=False)
            r.set("hot", value, ex=300)
            return value
        finally:
            r.delete("hot:lock")

    time.sleep(0.1)                                  # 没抢到就等一会儿再读
    return r.get("hot")


# ------------------------------------------------------------ 雪崩
def set_uniform_ttl(n: int = 20) -> None:
    """所有 key 用同一个 TTL, 会同一秒集体过期."""
    for i in range(n):
        r.set(f"avalanche:{i}", i, ex=60)


def set_jitter_ttl(n: int = 20) -> None:
    """TTL 加随机抖动, 过期时间就散开了."""
    for i in range(n):
        r.set(f"jitter:{i}", i, ex=60 + random.randint(0, 30))


if __name__ == "__main__":
    show("① 穿透: 查一个不存在的 id, 100 次")
    before = db.hits
    for _ in range(100):
        read_plain(999999)
    print("    数据库被查       ->", db.hits - before, "次  <- 缓存完全没用")

    show("② 防护后: 把空值也缓存起来")
    before = db.hits
    for _ in range(100):
        read_with_null(999999)
    print("    数据库被查       ->", db.hits - before, "次  <- 只有第一次")

    show("③ 击穿: 热点 key 不存在, 10 个线程同时来")
    r.delete("hot", "hot:lock")
    before = db.hits
    threads = [threading.Thread(target=read_no_lock, args=(1,)) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("    数据库被查       ->", db.hits - before, "次  <- 全部穿透")

    show("④ 防护后: 加互斥锁, 只放一个线程进去")
    r.delete("hot", "hot:lock")
    before = db.hits
    threads = [threading.Thread(target=read_with_lock, args=(1,)) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print("    数据库被查       ->", db.hits - before, "次  <- 只有拿到锁的那个")

    show("⑤ 雪崩: 20 个 key 用同一个 TTL")
    set_uniform_ttl()
    print("    前 5 个 key 的 ttl ->", [r.ttl(f"avalanche:{i}") for i in range(5)])
    print("    注: 完全一样, 会同一秒集体过期")

    show("⑥ 防护后: TTL 加随机抖动")
    set_jitter_ttl()
    print("    前 5 个 key 的 ttl ->", [r.ttl(f"jitter:{i}") for i in range(5)])
    print("    注: 被打散了")

    show("⑦ 三种问题对照")
    print("    穿透  查不存在的数据       -> 空值缓存 / 布隆过滤器 / 参数校验")
    print("    击穿  单个热点 key 过期    -> 互斥锁 / 逻辑过期 / 提前预热")
    print("    雪崩  大批 key 同时过期    -> TTL 抖动 / 多级缓存 / 熔断降级")

    show("⑧ 清理")
    r.delete("plain:999999", "null:999999", "hot", "hot:lock")
    for i in range(20):
        r.delete(f"avalanche:{i}", f"jitter:{i}")
    print("    已清理")
