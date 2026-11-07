"""Redis 第一章 - 案例 3: List, Set, ZSet.

三种结构解决三个不同问题:
    List = 排队的队伍(有序, 可重复)   -> 队列, 栈, 最近 N 条
    Set  = 一个名单(无序, 不重复)     -> 去重, 标签, 交集
    ZSet = 带分数的名单(按分数排序)   -> 排行榜

命令的命名规律(记住这四条就够):
    L = Left, R = Right      -> lpush 从左进, rpop 从右出
    S = Set                  -> sadd / smembers / sinter
    Z = 有序集合             -> zadd / zrange / zrank
    rev = reverse(倒序)       -> zrevrange = 从高到低
    inter = 交集, union = 并集, diff = 差集

怎么跑:
    python redis_notes/ch01/code/03_list_set_zset.py
"""

import redis

r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    # ---------------------------------------------------------------- List
    show("① List 当队列: 右边进, 左边出 (先进先出)")
    r.rpush("queue", "task-1", "task-2", "task-3")     # 从右边塞进三个
    print("    rpush 后 lrange     ->", r.lrange("queue", 0, -1))
    print("    lpop 取出最左边     ->", r.lpop("queue"))
    print("    剩余                ->", r.lrange("queue", 0, -1))
    print("    注: lrange 的 0 到 -1 表示从头到尾, -1 是最后一个")

    show("② List 当栈: 右边进, 右边出 (后进先出)")
    r.rpush("stack", "page-1", "page-2", "page-3")
    print("    rpush 后            ->", r.lrange("stack", 0, -1))
    print("    rpop 取出最右边     ->", r.rpop("stack"))
    print("    剩余                ->", r.lrange("stack", 0, -1))

    show("③ List 只留最近 5 条 (ltrim 裁剪)")
    for i in range(8):
        r.lpush("logs", f"log-{i}")        # 新的从左边塞
        r.ltrim("logs", 0, 4)              # 只保留第 0 到第 4 个
    print("    lrange 0 -1         ->", r.lrange("logs", 0, -1))
    print("    llen                ->", r.llen("logs"), "(永远是 5)")

    # ---------------------------------------------------------------- Set
    show("④ Set 去重与集合运算")
    r.sadd("tag:a", "python", "mysql", "redis")
    r.sadd("tag:b", "python", "redis", "docker")
    print("    A 的成员            ->", sorted(r.smembers("tag:a")))
    print("    B 的成员            ->", sorted(r.smembers("tag:b")))
    print("    sinter 交集         ->", sorted(r.sinter("tag:a", "tag:b")))
    print("    sunion 并集         ->", sorted(r.sunion("tag:a", "tag:b")))
    print("    sdiff A 独有        ->", sorted(r.sdiff("tag:a", "tag:b")))
    print("    sismember(python)   ->", r.sismember("tag:a", "python"), "(1 在, 0 不在)")
    print("    sadd 重复添加       ->", r.sadd("tag:a", "python"), "(0 表示已存在, 没加进去)")

    # ---------------------------------------------------------------- ZSet
    show("⑤ ZSet 排行榜: 每个成员带一个分数")
    r.zadd("rank", {"张三": 888, "李四": 400, "王五": 100})
    print("    zrange 正序         ->", r.zrange("rank", 0, -1, withscores=True))
    print("    zrevrange 倒序前三  ->", r.zrevrange("rank", 0, 2, withscores=True))
    print("    zrank 李四的排名    ->", r.zrank("rank", "李四"), "(从 0 开始, 分数低的在前)")
    print("    zscore 张三的分数   ->", r.zscore("rank", "张三"))
    r.zincrby("rank", 50, "王五")
    print("    王五加 50 后倒序    ->", r.zrevrange("rank", 0, -1, withscores=True))

    # ---------------------------------------------------------------- 对比
    show("⑥ 三种结构对比")
    print("    List  有序, 可重复, 两端进出     -> 队列, 栈, 消息流")
    print("    Set   无序, 不重复, 能算交并差   -> 标签, 点赞去重, 共同好友")
    print("    ZSet  不重复, 按分数排序         -> 排行榜, 热搜, 延时队列")

    show("⑦ 清理")
    for key in ("queue", "stack", "logs", "tag:a", "tag:b", "rank"):
        r.delete(key)
    print("    已删除 queue / stack / logs / tag:a / tag:b / rank")
