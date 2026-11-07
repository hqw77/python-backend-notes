# Redis 第一章 · Redis 基础

## 1.1 学习目标

这一章只讲 Redis 本身，不涉及项目改造。学完应该能做到：

1. 说清 Redis 是什么、和 MySQL 分工有什么不同
2. 知道五种数据类型各自解决什么问题
3. **看懂每个常用命令是什么意思、参数是什么、返回什么**
4. 会用 Python 连接 Redis 并读写数据
5. 知道缓存 key 必须设过期，以及几种 key 的管理命令

> **本章的读法**：每个数据类型都按"它是什么 → 命令表 → 跑一遍 → 一个坑"的顺序讲。
> 如果只想知道某个命令干什么，直接跳到 1.4 ~ 1.8 的命令表。

---

## 1.2 先把 Redis 是什么搞清楚

### 1.2.1 一句话定义

Redis 是一个**把数据放在内存里的键值数据库**。

- **键值**：所有数据都是 `key -> value` 的形式，跟 Python 的字典一样
- **内存**：数据不落磁盘，所以读写是微秒级

```python
r.set("name", "张三")     # key 是 name，value 是 张三
r.get("name")             # 取回来
```

### 1.2.2 Redis 和 MySQL 的分工

| | MySQL | Redis |
| --- | --- | --- |
| 数据放哪 | 磁盘 | 内存 |
| 读写速度 | 毫秒级 | 微秒级 |
| 数据量 | GB ~ TB | 受内存限制，通常几 GB |
| 断电会不会丢 | 不会 | 可能丢（虽然有持久化） |
| **定位** | **唯一可信来源** | **加速层，丢了能重建** |

这条必须记住：**Redis 里的数据必须能从 MySQL 重新算出来**。凡是"只存在 Redis、丢了就没了"的数据，都不能只放 Redis。

> **通俗理解**：MySQL 是仓库，东西全但取货慢；Redis 是收银台旁边的货架，只放卖得最快的几样。货架被搬空了不要紧，回仓库再拿一趟就行。

### 1.2.3 为什么单线程还这么快

Redis 处理命令是**单线程**的，但依然很快，原因：

1. 数据在内存，不用等磁盘
2. 每条命令都很简单，耗时在微秒级
3. 单线程省掉了加锁和线程切换的开销

**副作用（也是好处）**：因为一次只处理一条命令，所以单条命令天然是原子的，不用担心并发改同一份数据。

> **通俗理解**：一个窗口只开一个收银员，但每笔交易只要 1 微秒。开十个收银员反而要协调谁先谁后。

---

## 1.3 五种数据类型：先看全景

### 1.3.1 一张表看懂

| 类型 | 一句话 | 典型用途 | 命令开头字母 |
| --- | --- | --- | --- |
| **String** | 一个 key 对应一个值 | 缓存对象、计数器、分布式锁 | 没有前缀：`set` / `get` / `incr` |
| **Hash** | 一个 key 里再分字段 | 存一个对象的多个属性 | `h`：`hset` / `hget` |
| **List** | 有序列表，两端进出 | 队列、栈、最近 N 条 | `l` / `r`：`lpush` / `rpop` |
| **Set** | 无序，自动去重 | 标签、点赞去重、交集 | `s`：`sadd` / `sinter` |
| **ZSet** | 每个成员带分数，按分数排序 | 排行榜、热搜、延时队列 | `z`：`zadd` / `zrange` |

### 1.3.2 命令的命名规律

记住这几条，看到命令就能猜出意思：

| 规律 | 含义 | 例子 |
| --- | --- | --- |
| **L / R** | Left 左端 / Right 右端 | `lpush` 左进，`rpop` 右出 |
| **S 开头** | Set 集合 | `sadd` 添加，`sinter` 交集 |
| **Z 开头** | ZSet 有序集合 | `zadd` 添加，`zrank` 排名 |
| **H 开头** | Hash 哈希 | `hset` 设置字段 |
| **REV** | Reverse 倒序 | `zrevrange` 从高到低 |
| **INTER / UNION / DIFF** | 交集 / 并集 / 差集 | `sinter` / `sunion` / `sdiff` |
| **CARD** | Cardinality 基数（元素个数） | `scard` / `zcard` |
| **TTL** | Time To Live 剩余存活时间 | `ttl` / `expire` |

> **通俗理解**：Redis 的命令名几乎是"全大写英文单词的缩写"。知道 `inter` 是交集、`rev` 是倒序，一半的命令就不用背了。

---

## 1.4 String：最基础的类型

### 1.4.1 是什么

一个 key 对应一个值。值可以是字符串、数字、JSON 文本。

```plain
   key             value
   name     ->     张三
   visits   ->     106
   user:1   ->     {"id":1,"name":"张三"}     ← 对象要自己转成 JSON 字符串
```

### 1.4.2 命令表

| 命令 | 中文意思 | 怎么用 | 返回什么 |
| --- | --- | --- | --- |
| `set(k, v)` | 存一个值（会覆盖旧值） | `set("name", "张三")` | `True` |
| `get(k)` | 取值 | `get("name")` | 值；key 不存在返回 `None` |
| `set(k, v, ex=秒)` | 存值并设置过期 | `set("code", "8888", ex=60)` | `True` |
| `set(k, v, px=毫秒)` | 同上，毫秒级 | `set("code", "8888", px=5000)` | `True` |
| `set(k, v, nx=True)` | **只有 key 不存在才写** | `set("lock", "A", nx=True)` | 成功 `True`；已存在返回 `None` |
| `mset({...})` | 一次存多个 | `mset({"a": 1, "b": 2})` | `True` |
| `mget(k1, k2)` | 一次取多个 | `mget("a", "b")` | 列表，不存在的位是 `None` |
| `incr(k)` | 数字 +1 | `incr("visits")` | 加完后的新值 |
| `incrby(k, n)` | 数字 +n | `incrby("visits", 10)` | 新值 |
| `decrby(k, n)` | 数字 -n | `decrby("visits", 5)` | 新值 |
| `append(k, s)` | 在值后面追加 | `append("name", "同学")` | 追加后的长度 |
| `strlen(k)` | 值的长度 | `strlen("name")` | 整数 |

**关于 `incr` 为什么要单独记**：它是**原子操作**，直接让 Redis 自己加。不像 MySQL 那样"读出来 +1 再写回"，所以并发时不会丢更新（第五章踩过那个坑）。

### 1.4.3 跑一遍

案例文件：`redis_notes/ch01/code/02_string_hash.py`

```plain
--- ① String: 存一个值,取一个值 ---
    get('name')        -> 张三
    get('nobody')      -> None (不存在就是 None)

--- ② String: 计数器, INCR 是原子的 ---
    初始               -> 100
    incr               -> 101
    incrby(10)         -> 111
    decrby(5)          -> 106
    注: 不用先读再写,所以不会像 MySQL 那样丢更新

--- ③ String: 只有 key 不存在才写入(SET NX) ---
    第一次 set nx       -> True
    第二次 set nx       -> None (None 表示没抢到)
    锁的持有者          -> A
    剩余秒数            -> 10
```

### 1.4.4 一个坑：`nx` 返回 None 不是 False

```python
r.set("lock", "A", nx=True)    # True  抢到了
r.set("lock", "B", nx=True)    # None  没抢到
```

注意是 `None` 而不是 `False`。写判断时要写 `if r.set(k, v, nx=True):`——`None` 在条件判断里是假，所以这样写是对的，但别写成 `if ... is False`。

---

## 1.5 Hash：存一个对象的多个字段

### 1.5.1 是什么

一个 key 里面再分多组"字段 -> 值"，像一个小表格。

```plain
   key      field       value
   user:1   username -> 张三
            phone    -> 13800000001
            points   -> 12
```

和"把对象转成 JSON 存成 String"的区别：Hash 可以**只改其中一个字段**。

### 1.5.2 命令表

| 命令 | 中文意思 | 怎么用 | 返回什么 |
| --- | --- | --- | --- |
| `hset(k, field, v)` | 设置一个字段 | `hset("user:1", "username", "张三")` | 新增的字段数 |
| `hset(k, mapping={...})` | 一次设置多个字段 | `hset("user:1", mapping={"a": 1})` | 新增的字段数 |
| `hget(k, field)` | 取一个字段 | `hget("user:1", "username")` | 值；没有返回 `None` |
| `hgetall(k)` | 取全部字段 | `hgetall("user:1")` | 字典 |
| `hdel(k, field)` | 删一个字段 | `hdel("user:1", "phone")` | 删掉了几个 |
| `hincrby(k, field, n)` | 字段值加 n（**只能整数**） | `hincrby("user:1", "points", 12)` | 新值 |
| `hkeys(k)` | 所有字段名 | `hkeys("user:1")` | 列表 |
| `hvals(k)` | 所有字段值 | `hvals("user:1")` | 列表 |
| `hlen(k)` | 有几个字段 | `hlen("user:1")` | 整数 |
| `hexists(k, field)` | 字段存在吗 | `hexists("user:1", "phone")` | `True` / `False` |

### 1.5.3 跑一遍

```plain
--- ④ Hash: 存一个对象 ---
    hgetall            -> {'username': '张三', 'phone': '13800000001', 'points': '0'}
    hget(username)     -> 张三
    hincrby(points,12) -> 12
    注: hincrby 只能加整数,金额这种小数会报错
```

### 1.5.4 一个坑：`hincrby` 对小数会报错

```python
r.hset("user:1", "balance", "888.00")
r.hincrby("user:1", "balance", 12)     # 报错: hash value is not an integer
```

因为 Redis 的 `incr` 系列**只支持整数**。金额要用 String 存，在 Python 里用 `Decimal` 算好再写回。

### 1.5.5 String 还是 Hash？

| 需求 | 选 |
| --- | --- |
| 存一个值、做计数、做锁 | String |
| 存对象，且经常只改一个字段 | Hash |
| 整个对象要一起设过期时间 | String + JSON（Hash 不能给单个字段设过期） |

---

## 1.6 List：队列与栈

### 1.6.1 是什么

一个有序的列表，**两端都能进出**。可以重复。

```plain
   LPUSH 在左边塞           RPUSH 在右边塞
   ┌───┬───┬───┐
   │ A │ B │ C │
   └───┴───┴───┘
     ↑           ↑
   LPOP 左边取  RPOP 右边取
```

### 1.6.2 两种用法

| 用法 | 怎么进出 | 效果 |
| --- | --- | --- |
| **队列**（FIFO） | 右进 `rpush` + 左出 `lpop` | 先进先出 |
| **栈**（LIFO） | 右进 `rpush` + 右出 `rpop` | 后进先出 |

### 1.6.3 命令表

| 命令 | 中文意思 | 怎么用 | 返回什么 |
| --- | --- | --- | --- |
| `lpush(k, *v)` | 从**左边**塞进去 | `lpush("queue", "a", "b")` | 塞完后的长度 |
| `rpush(k, *v)` | 从**右边**塞进去 | `rpush("queue", "a")` | 长度 |
| `lpop(k)` | 从左边取出一个（取出就删了） | `lpop("queue")` | 取出的值；空了返回 `None` |
| `rpop(k)` | 从右边取出一个 | `rpop("queue")` | 同上 |
| `lrange(k, 0, -1)` | 看区间内的元素（不出栈） | `lrange("queue", 0, -1)` | 列表 |
| `llen(k)` | 长度 | `llen("queue")` | 整数 |
| `ltrim(k, 0, 4)` | **只保留**这个区间，其余删掉 | `ltrim("logs", 0, 4)` | `True` |
| `lindex(k, 0)` | 取第 n 个（不删） | `lindex("queue", 0)` | 值 |
| `blpop(k, timeout=5)` | 阻塞版 lpop：没数据就等 | — | 有数据即刻返回 |

**`lrange` 的 0 和 -1**：`-1` 表示最后一个元素，所以 `0, -1` 就是"从头到尾"。

### 1.6.4 跑一遍

```plain
--- ① List 当队列: 右边进, 左边出 (先进先出) ---
    rpush 后 lrange     -> ['task-1', 'task-2', 'task-3']
    lpop 取出最左边     -> task-1
    剩余                -> ['task-2', 'task-3']

--- ② List 当栈: 右边进, 右边出 (后进先出) ---
    rpush 后            -> ['page-1', 'page-2', 'page-3']
    rpop 取出最右边     -> page-3
    剩余                -> ['page-1', 'page-2']

--- ③ List 只留最近 5 条 (ltrim 裁剪) ---
    lrange 0 -1         -> ['log-7', 'log-6', 'log-5', 'log-4', 'log-3']
    llen                -> 5 (永远是 5)
```

### 1.6.5 一个技巧：用 `ltrim` 防止列表无限增长

```python
r.lpush("logs", f"log-{i}")
r.ltrim("logs", 0, 4)      # 只保留最新的 5 条
```

日志、消息流、最近浏览记录都该这么写，否则列表会一直变长，把内存吃光。

---

## 1.7 Set：去重与集合运算

### 1.7.1 是什么

一个**无序、不重复**的集合。

```plain
   tag:a  ->  {python, mysql, redis}
   tag:b  ->  {python, redis, docker}
```

重复添加同一个元素不会报错，只是不生效。

### 1.7.2 命令表

| 命令 | 中文意思 | 怎么用 | 返回什么 |
| --- | --- | --- | --- |
| `sadd(k, *v)` | 添加元素 | `sadd("tag:a", "python")` | 新加进去了几个（重复的算 0） |
| `srem(k, *v)` | 移除元素 | `srem("tag:a", "python")` | 删掉了几个 |
| `smembers(k)` | 所有元素 | `smembers("tag:a")` | 集合（可转 list） |
| `sismember(k, v)` | 这个元素在不在 | `sismember("tag:a", "python")` | `1` 在 / `0` 不在 |
| `sinter(k1, k2)` | **交集**：两边都有 | `sinter("tag:a", "tag:b")` | 集合 |
| `sunion(k1, k2)` | **并集**：合在一起去重 | `sunion("tag:a", "tag:b")` | 集合 |
| `sdiff(k1, k2)` | **差集**：k1 有而 k2 没有 | `sdiff("tag:a", "tag:b")` | 集合 |
| `scard(k)` | 元素个数 | `scard("tag:a")` | 整数 |

**记忆**：`inter` = intersection 交集，`union` = 并集，`diff` = difference 差集。

### 1.7.3 跑一遍

```plain
--- ④ Set 去重与集合运算 ---
    A 的成员            -> ['mysql', 'python', 'redis']
    B 的成员            -> ['docker', 'python', 'redis']
    sinter 交集         -> ['python', 'redis']
    sunion 并集         -> ['docker', 'mysql', 'python', 'redis']
    sdiff A 独有        -> ['mysql']
    sismember(python)   -> 1 (1 在, 0 不在)
    sadd 重复添加       -> 0 (0 表示已存在, 没加进去)
```

### 1.7.4 典型场景

| 场景 | 用什么命令 |
| --- | --- |
| 文章标签 | `sadd` 加标签，`smembers` 查标签 |
| 点赞去重 | `sadd` + `scard` 数总数 |
| 共同好友 | `sinter` 两人好友集合的交集 |
| 抽奖去重 | `sadd` 返回 0 说明已经参与过 |

---

## 1.8 ZSet：排行榜

### 1.8.1 是什么

和 Set 一样不重复，但每个成员带一个**分数（score）**，Redis 会按分数自动排序。

```plain
   rank  ->  张三: 888
             李四: 400
             王五: 100
```

### 1.8.2 命令表

| 命令 | 中文意思 | 怎么用 | 返回什么 |
| --- | --- | --- | --- |
| `zadd(k, {成员: 分数})` | 添加成员和分数 | `zadd("rank", {"张三": 888})` | 新加进去了几个 |
| `zrange(k, 0, -1)` | 按分数**从小到大**取 | `zrange("rank", 0, -1)` | 列表 |
| `zrange(..., withscores=True)` | 连分数一起返回 | `zrange("rank", 0, -1, withscores=True)` | `[(成员, 分数), ...]` |
| `zrevrange(k, 0, 2)` | 按分数**从大到小**取前 3 | `zrevrange("rank", 0, 2)` | 列表 |
| `zrank(k, 成员)` | 排名（从小到大，从 0 开始） | `zrank("rank", "李四")` | 整数 |
| `zrevrank(k, 成员)` | 排名（从大到小） | `zrevrank("rank", "张三")` | 整数 |
| `zscore(k, 成员)` | 查某个成员的分数 | `zscore("rank", "张三")` | 分数 |
| `zincrby(k, n, 成员)` | 给某个成员加 n 分 | `zincrby("rank", 50, "王五")` | 新分数 |
| `zrangebyscore(k, 低, 高)` | 取分数在区间内的成员 | `zrangebyscore("rank", 100, 500)` | 列表 |
| `zrem(k, 成员)` | 移除成员 | `zrem("rank", "王五")` | 删掉了几个 |
| `zcard(k)` | 有几个成员 | `zcard("rank")` | 整数 |

### 1.8.3 跑一遍

```plain
--- ⑤ ZSet 排行榜: 每个成员带一个分数 ---
    zrange 正序         -> [('王五', 100.0), ('李四', 400.0), ('张三', 888.0)]
    zrevrange 倒序前三  -> [('张三', 888.0), ('李四', 400.0), ('王五', 100.0)]
    zrank 李四的排名    -> 1 (从 0 开始, 分数低的在前)
    zscore 张三的分数   -> 888.0
    王五加 50 后倒序    -> [('张三', 888.0), ('李四', 400.0), ('王五', 150.0)]
```

### 1.8.4 一个注意点：分数是浮点数，排名从 0 开始

- `zscore` 返回 `888.0` 而不是 `888`，是浮点数
- `zrank` 从 0 开始：第 1 名返回 0，第 2 名返回 1
- 分数相同时，按成员的字典序排

---

## 1.9 怎么选：一张决策表

| 你要存的东西 | 选 | 理由 |
| --- | --- | --- |
| 一个值、一个计数、一把锁 | String | 最简单，`incr` 原子 |
| 一个对象，经常只改某个字段 | Hash | 不用整体覆盖 |
| 一个对象，整体读写、要设过期 | String + JSON | Hash 不能给字段设过期 |
| 排队、任务队列 | List | `rpush` + `lpop` |
| 最近 N 条记录 | List + `ltrim` | 自动截断 |
| 标签、去重、共同好友 | Set | 自动去重 + 集合运算 |
| 排行榜、热搜 | ZSet | 按分数排序 |

> **通俗理解**：先问自己"这东西是一串还是一个对象"，再问"要不要排序/去重"，答案基本就出来了。

---

## 1.10 key 的管理

### 1.10.1 过期相关

| 命令 | 中文意思 | 怎么用 | 返回什么 |
| --- | --- | --- | --- |
| `set(k, v, ex=秒)` | 存值同时设过期（推荐） | `set("code", "8888", ex=60)` | `True` |
| `expire(k, 秒)` | 给**已有** key 设过期 | `expire("session", 30)` | `True` |
| `ttl(k)` | 还剩多少秒 | `ttl("session")` | 见下表 |
| `persist(k)` | 去掉过期，变永久 | `persist("code")` | `True` |

**`ttl` 的三种返回值，一定要记住**：

| 返回 | 含义 | 处理 |
| --- | --- | --- |
| `-2` | key 不存在（或已过期） | 正常 |
| `-1` | 存在，但**永不过期** | 缓存 key 出现 -1 是危险信号 |
| 正整数 | 还剩几秒 | 正常 |

```plain
--- ③ ttl 的三种返回值 ---
    key 不存在           -> -2 (-2 表示没有这个 key)
    没设过期             -> -1 (-1 表示永不过期)
    设了过期             -> 60 (正数, 还剩几秒)
```

### 1.10.2 过期不是"到点就消失"

Redis 清理过期 key 用两种策略：

1. **访问时检查**：你 `get` 一个 key，它发现过期了就删掉
2. **定期抽样**：每秒随机抽一些 key 检查

所以 key 过期后，**内存不会立刻释放**。

```plain
--- ⑤ 过期是被动的: 到点不会立刻消失 ---
    刚设置               -> v
    等 0.5 秒后          -> None (已经读不到了)
    ttl                  -> -2 (-2 表示这个 key 没了)
```

### 1.10.3 遍历与删除

| 命令 | 中文意思 | 注意 |
| --- | --- | --- |
| `scan_iter("user:*")` | 按模式遍历 key | **生产环境只用这个** |
| `keys("*")` | 按模式查 key | **禁用**：一次性扫描全库，会卡住服务 |
| `delete(k)` / `del` | 同步删除 | 小 key 用 |
| `unlink(k)` | 异步删除 | 大 key（几十万元素）用，后台回收内存 |
| `exists(k)` | 存在吗 | 返回 1 / 0 |
| `type(k)` | 什么类型 | 返回 string / hash / list / set / zset |
| `dbsize()` | 当前库有几个 key | — |
| `flushdb()` | 清空当前库 | ⚠️ 危险，学习环境才用 |

```plain
--- ⑥ 遍历 key: 用 scan, 不要用 keys ---
    scan 匹配 item:*     -> ['item:0', 'item:1', 'item:2', 'item:3', 'item:4']

--- ⑦ 删除: del 是同步, unlink 是异步 ---
    del item:0           -> 1 (返回删掉了几个)
    unlink item:1        -> 1 (大 key 用这个, 后台回收内存)
```

### 1.10.4 命名规范

```plain
业务:对象:标识          user:42    order:2024:88    article:1001:views
带环境前缀              prod:user:42    dev:user:42
```

三个好处：可读、能按前缀批量管理（`scan_iter("user:*")`）、不会和别的业务撞名。

---

## 1.11 用 Python 连接 Redis

### 1.11.1 安装与两种连法

```bash
pip install redis
```

```python
import redis

# ① 单连接：用一次就关
r = redis.Redis(host="127.0.0.1", port=6379, db=0, decode_responses=True)
r.close()

# ② 连接池：建一个池子反复借用（推荐）
pool = redis.ConnectionPool(host="127.0.0.1", port=6379, db=0,
                            decode_responses=True, max_connections=20)
client = redis.Redis(connection_pool=pool)
```

和第二章的 MySQL 连接池是一个道理：**建连接有网络开销，复用才划算**。

### 1.11.2 `decode_responses` 必须开

```plain
--- ④ decode_responses 的作用 ---
    decode=False      -> b'\xe4\xbd\xa0\xe5\xa5\xbd' (bytes, 要自己 decode)
    decode=True       -> 你好 (str, 直接能用)
```

Redis 存的本来就是字节。`decode_responses=True` 让客户端自动解码成字符串，省得每处都写 `.decode()`。

### 1.11.3 存对象要先序列化

Redis 只能存字符串，所以对象要自己转：

```python
import json

r.set("user:42", json.dumps({"id": 42, "name": "张三"}, ensure_ascii=False), ex=300)
data = json.loads(r.get("user:42"))
```

`ensure_ascii=False` 让中文原样存，否则会变成 `\u5f20\u4e09`，用 `redis-cli` 看的时候很难受。

---

## 1.12 常见错误

| 报错 / 现象 | 原因 | 解决 |
| --- | --- | --- |
| `ConnectionRefusedError` | Redis 没启动 | `docker start mysql-learn-redis` |
| `hash value is not an integer` | 对小数用了 `hincrby` | 金额用 String 存，在 Python 里算 |
| `bytes` 不能 `json.loads` | 没开 `decode_responses` | 连接时加该参数 |
| `WRONGTYPE Operation against a key` | 同一个 key 先当 String 又当 Hash | 不同类型用不同 key 名 |
| 内存一直涨 | key 没设过期 | 所有缓存 key 必须带 `ex` |
| 线上突然卡顿 | 用了 `keys *` | 改用 `scan_iter` |
| `nx` 判断写错 | 以为返回 `False` | 实际返回 `None`，用真假判断即可 |

---

## 1.13 本章小结

1. Redis 是内存键值库，定位是**加速层**，数据必须能从 MySQL 重建。
2. 五种类型的分工：String 存值与计数、Hash 存对象、List 做队列、Set 去重、ZSet 排行。
3. 命令命名有规律：L/R 表示左右端，S/Z/H 表示类型，REV 是倒序，INTER/UNION/DIFF 是交并差。
4. `incr` / `hincrby` 是原子的，但**只支持整数**；金额要另想办法。
5. `ttl` 返回 `-1` 表示永不过期，这是缓存 key 的隐患。
6. 遍历用 `scan_iter`，不要用 `keys`；大 key 用 `unlink` 删。
7. Python 侧用连接池 + `decode_responses=True`，对象用 JSON 序列化。

---

## 1.14 练习

1. 用 String 实现"同一用户 60 秒内只能发一次验证码"（提示：`set nx` + `ex`）。
2. 用 Hash 存一个用户资料，要求能单独改手机号而不动其他字段。
3. 用 List 实现"只保留最近 100 条日志"，写出压入和裁剪两行代码。
4. 用 ZSet 实现"游戏排行榜"：能取前 10 名、能查某人排名、能给某人加分。
5. 思考：为什么缓存 key 如果 `ttl` 返回 `-1` 很危险？

---

<small>相关:[第二章 -- 缓存设计与三大问题](../../ch02/notes/缓存设计与三大问题.md) · [返回 Redis 目录](../../README.md)</small>
