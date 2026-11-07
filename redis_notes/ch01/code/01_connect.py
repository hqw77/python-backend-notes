"""Redis 第一章 - 案例 1: 连接与连接池.

Redis 是"客户端 - 服务端"结构, 你的 Python 程序是客户端.
每次操作都要先有一条到 Redis 的连接, 建连接有成本, 所以要复用.

怎么跑:
    python redis_notes/ch01/code/01_connect.py
"""

import redis

# 连接参数: 地址, 端口, 第几个库(0~15), 是否自动解码成字符串
HOST = "127.0.0.1"
PORT = 6379


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    show("① 单连接: 用一次就关")
    r = redis.Redis(host=HOST, port=PORT, db=0, decode_responses=True)
    print("    ping()            ->", r.ping(), "(True 表示服务活着)")
    r.close()

    show("② 连接池: 建一个池子, 反复借用")
    pool = redis.ConnectionPool(
        host=HOST, port=PORT, db=0, decode_responses=True, max_connections=20
    )
    client = redis.Redis(connection_pool=pool)
    print("    ping()            ->", client.ping())
    print("    池子最大连接数    ->", pool.max_connections)

    show("③ 服务端信息")
    info = client.info()
    print("    redis 版本        ->", info["redis_version"])
    print("    已用内存          ->", info["used_memory_human"])

    show("④ decode_responses 的作用")
    raw = redis.Redis(host=HOST, port=PORT, db=0)          # 默认 False
    raw.set("hello", "你好")
    print("    decode=False      ->", raw.get("hello"), "(bytes, 要自己 decode)")
    print("    decode=True       ->", client.get("hello"), "(str, 直接能用)")
    raw.delete("hello")
    raw.close()

    show("⑤ 当前库里有几个 key")
    print("    dbsize()          ->", client.dbsize())

    client.close()
    print("\n完成. 单连接用完要 close, 池子由整个进程共用.")
