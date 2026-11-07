"""Redis 第二章 - 案例 3: 先删缓存还是先改库.

两种写路径的区别:
    路径 A(错): 先删缓存 -> 读线程把旧值写回 -> 再改库  => 缓存一直是旧值
    路径 B(对): 先改库 -> 再删缓存                        => 最多短暂旧值, 随后自愈

用"分步模拟"代替真实并发, 每一步都把数据库和缓存的状态打印出来.

怎么跑:
    python redis_notes/ch02/code/03_consistency.py
"""

import json

import redis

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
KEY = "user:1"


def show(title: str) -> None:
    print(f"\n--- {title} ---")


def cache_text() -> str:
    raw = r.get(KEY)
    return raw if raw else "None"


def state(tag: str, db_value: str) -> None:
    print(f"    {tag:10} 数据库={db_value:8} 缓存={cache_text()}")


def reset() -> None:
    r.set(KEY, json.dumps({"id": 1, "balance": "888.00"}, ensure_ascii=False), ex=300)


if __name__ == "__main__":
    # ================================================== 路径 A: 先删缓存
    show("① 路径 A: 先删缓存, 再改数据库(有问题的写法)")
    reset()
    state("初始", "888.00")

    print("    写线程: 先删除缓存")
    r.delete(KEY)
    state("删缓存后", "888.00")

    print("    读线程: 缓存没了 -> 查库拿到旧值 888 -> 写回缓存")
    r.set(KEY, json.dumps({"id": 1, "balance": "888.00"}, ensure_ascii=False), ex=300)
    state("读回写后", "888.00")

    print("    写线程: 现在才把数据库改成 588")
    state("改库后", "588.00")
    print("    !! 缓存还是 888, 数据库是 588, 脏数据会一直留到过期")

    # ================================================== 路径 B: 先改库
    show("② 路径 B: 先改数据库, 再删缓存(推荐写法)")
    reset()
    state("初始", "888.00")

    print("    写线程: 先把数据库改成 588")
    state("改库后", "588.00")

    print("    写线程: 再删除缓存")
    r.delete(KEY)
    state("删缓存后", "588.00")

    print("    读线程: 未命中 -> 查库拿到 588 -> 写回")
    r.set(KEY, json.dumps({"id": 1, "balance": "588.00"}, ensure_ascii=False), ex=300)
    state("读回写后", "588.00")
    print("    OK 最坏情况只是有人短暂读到旧值, 之后会自愈")

    show("③ 为什么是删缓存, 而不是更新缓存")
    print("    更新缓存: 两个写者先后更新, 顺序错乱时可能写进旧值")
    print("    删除缓存: 下次读自然重建, 逻辑简单, 出错概率低")

    show("④ 删缓存失败怎么办")
    print("    方案一: 延迟双删 -- 改库后 delete, 等 500ms 再 delete 一次")
    print("    方案二: 把删除操作丢进消息队列, 失败了自动重试")
    print("    方案三: 给缓存设短 TTL 兜底, 最多脏几分钟")

    show("⑤ 清理")
    r.delete(KEY)
    print("    已清理")
