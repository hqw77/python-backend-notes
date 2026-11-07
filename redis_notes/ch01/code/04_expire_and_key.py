"""Redis 第一章 - 案例 4: 过期时间与 key 管理.

缓存的 key 必须有过期时间, 否则内存会被慢慢吃光.
另外 key 的命名, 遍历, 删除都有讲究, 这个案例把这几点跑一遍.

怎么跑:
    python redis_notes/ch01/code/04_expire_and_key.py
"""

import time

import redis

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    show("① 给已有的 key 设置过期(expire)")
    r.set("session", "abc123")
    print("    刚 set 完 ttl        ->", r.ttl("session"), "(-1 表示永不过期)")
    r.expire("session", 30)
    print("    expire 30 后 ttl     ->", r.ttl("session"), "(还剩多少秒)")
    print("    注: 缓存的 key 出现 -1 是危险信号, 说明它永远不会被回收")

    show("② set 的时候直接带过期(推荐)")
    r.set("code", "8888", ex=60)          # ex = 秒
    print("    set ex=60 后 ttl     ->", r.ttl("code"))
    r.set("code2", "9999", px=5000)       # px = 毫秒
    print("    set px=5000 后 ttl   ->", r.ttl("code2"))

    show("③ ttl 的三种返回值")
    print("    key 不存在           ->", r.ttl("nothing"), "(-2 表示没有这个 key)")
    r.set("forever", "x")
    print("    没设过期             ->", r.ttl("forever"), "(-1 表示永不过期)")
    print("    设了过期             ->", r.ttl("code"), "(正数, 还剩几秒)")

    show("④ persist: 去掉过期, 变成永久")
    r.persist("code")
    print("    persist 后 ttl       ->", r.ttl("code"))

    show("⑤ 过期是被动的: 到点不会立刻消失")
    r.set("short", "v", px=300)           # 300 毫秒后过期
    print("    刚设置               ->", r.get("short"))
    time.sleep(0.5)
    print("    等 0.5 秒后          ->", r.get("short"), "(已经读不到了)")
    print("    ttl                  ->", r.ttl("short"), "(-2 表示这个 key 没了)")
    print("    注: Redis 靠'访问时检查 + 定期抽样'清理, 内存不会立刻释放")

    show("⑥ 遍历 key: 用 scan, 不要用 keys")
    for i in range(5):
        r.set(f"item:{i}", i)
    print("    scan 匹配 item:*     ->", sorted(r.scan_iter("item:*")))
    print("    注: keys * 会一次性扫描全库, 生产环境会卡住整个服务")

    show("⑦ 删除: del 是同步, unlink 是异步")
    print("    del item:0           ->", r.delete("item:0"), "(返回删掉了几个)")
    print("    unlink item:1        ->", r.unlink("item:1"), "(大 key 用这个, 后台回收内存)")

    show("⑧ key 的命名规范")
    print("    推荐: 业务:对象:标识   -> user:42   order:2024:88")
    print("    加环境: prod:user:42   -> 同一台 Redis 上区分测试和生产")
    print("    不要: user42 这种没分隔的, 以后没法按前缀批量管理")

    show("⑨ 清理")
    for key in ("session", "code", "code2", "forever", "short",
                "item:0", "item:1", "item:2", "item:3", "item:4"):
        r.delete(key)
    print("    已清理")
