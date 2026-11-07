"""Redis 第一章 - 案例 2: String 与 Hash.

String 适合存单个值,做计数器; Hash 适合存一个对象的多个字段.

怎么跑:
    python redis_notes/ch01/code/02_string_hash.py
"""

import redis

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    show("① String: 存一个值,取一个值")
    r.set("name", "张三")
    print("    get('name')        ->", r.get("name"))
    print("    get('nobody')      ->", r.get("nobody"), "(不存在就是 None)")

    show("② String: 计数器, INCR 是原子的")
    r.set("visits", 100)
    print("    初始               ->", r.get("visits"))
    print("    incr               ->", r.incr("visits"))
    print("    incrby(10)         ->", r.incrby("visits", 10))
    print("    decrby(5)          ->", r.decrby("visits", 5))
    print("    注: 不用先读再写,所以不会像 MySQL 那样丢更新")

    show("③ String: 只有 key 不存在才写入(SET NX)")
    print("    第一次 set nx       ->", r.set("lock", "A", nx=True, ex=10))
    print("    第二次 set nx       ->", r.set("lock", "B", nx=True, ex=10), "(None 表示没抢到)")
    print("    锁的持有者          ->", r.get("lock"))
    print("    剩余秒数            ->", r.ttl("lock"))

    show("④ Hash: 存一个对象")
    r.hset("user:1", mapping={"username": "张三", "phone": "13800000001", "points": "0"})
    print("    hgetall            ->", r.hgetall("user:1"))
    print("    hget(username)     ->", r.hget("user:1", "username"))
    print("    hincrby(points,12) ->", r.hincrby("user:1", "points", 12))
    print("    注: hincrby 只能加整数,金额这种小数会报错")

    show("⑤ 怎么选")
    print("    存一个值 / 做计数 / 做锁      -> String")
    print("    存对象,且经常只改一个字段    -> Hash")
    print("    整个对象要设过期时间          -> String + JSON(Hash 不能给单个字段设过期)")

    show("⑥ 清理")
    for key in ("name", "visits", "lock", "user:1"):
        r.delete(key)
    print("    已删除 name / visits / lock / user:1")
