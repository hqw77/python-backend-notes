# 生产化改造方案（内部系统 · 单机部署）

> 定位：**公司内部系统，几十到几百人使用，单台云服务器 + Docker Compose。**
> 这个定位决定了"做什么"和"不做什么"——不符合定位的复杂度一律不做。

## 1. 现状与目标

### 1.1 现在是什么

一个功能完整的学习项目：13 个接口、45 个测试、Docker 可一条命令启动。

### 1.2 目标是什么

**能稳定跑半年不出事，出事能在 10 分钟内定位，数据丢了能恢复。**

注意不是"高并发""高可用"——内部系统不需要。目标是**不出事故，出了能兜住**。

### 1.3 明确不做什么

| 不做 | 理由 |
| --- | --- |
| Kubernetes | 单机 Docker Compose 够了，K8s 只会增加运维负担 |
| 分库分表 | 内部系统数据量到不了那个量级 |
| 分布式追踪（链路追踪） | 单服务，日志带 request_id 就够 |
| 微服务拆分 | 一个服务解决的事，拆开只是自找麻烦 |
| 多活/异地容灾 | 成本远超收益 |
| 消息队列 | 现有 BackgroundTasks 够用 |

---

## 2. 现状审计

| 检查项 | 当前状态 | 风险 |
| --- | --- | --- |
| JWT 密钥 | 代码里有 dev 默认值 | 🔴 忘改就上线，令牌可被伪造 |
| 数据库/Redis 密码 | 默认空字符串 | 🔴 空密码等于裸奔 |
| CORS | 完全没配 | 🔴 前端跨域直接失败 |
| 登录限流 | 无 | 🔴 可被暴力破解 |
| `orders.user_id` 索引 | 无 | 🟠 查订单会全表扫描 |
| `users.is_deleted` 索引 | 无 | 🟠 列表每页都在过滤 |
| 转账并发 | 读-改-写，会丢更新 | 🔴 涉及金额，必须修 |
| 软删 + 唯一索引 | 删除后用户名被占用 | 🟠 用户投诉点 |
| 日志脱敏 | 未做 | 🟠 手机号、令牌可能落盘 |
| 备份 | 无 | 🔴 磁盘挂了数据全没 |
| 请求体大小 | 无限制 | 🟡 大包攻击 |
| 优雅关闭 | 已有 `engine.dispose()` | ✅ |
| 健康检查 | `/health`、`/health/db` | ✅ 够用 |

---

## 3. P0：上线前必须完成（8 项）

### P0-1 配置校验与密钥管理

**问题**：生产环境用了默认密钥不会报错，静默上线。

**做法**：

```python
# app/core/config.py
env: str = "dev"            # dev / prod

@model_validator(mode="after")
def check_prod(self):
    if self.env == "prod":
        if len(self.jwt_secret) < 32 or "dev-secret" in self.jwt_secret:
            raise ValueError("生产环境必须配置独立的 JWT_SECRET(>=32 字节)")
        if not self.mysql_password:
            raise ValueError("生产环境必须配置 MYSQL_PASSWORD")
    return self
```

**启动时校验，配置不对直接起不来**——这比"上线后才发现"好一万倍。

**验收**：`ENV=prod` 且不配置密钥时，容器启动失败并打印明确原因。

**工作量**：1 小时

---

### P0-2 CORS 白名单

**问题**：没配 CORS，前端调不通。

**做法**：

```python
allow_origins=settings.cors_origins    # 从配置读，逗号分隔
```

**不要用 `allow_origins=["*"]`**——内部系统有明确的域名。

**验收**：前端域名能调通，其他域名被浏览器拦住。

**工作量**：30 分钟

---

### P0-3 登录限流

**问题**：密码可被暴力破解。

**做法**：用已有的 Redis 做计数，不引入新框架。

```plain
   key: login:fail:{username}
   每次登录失败 INCR，并设置 15 分钟过期
   失败 >= 5 次 -> 直接返回 429，不再校验密码
   登录成功 -> 删除这个 key
```

**验收**：连续错 5 次后第 6 次返回 429。

**工作量**：2 小时（含测试）

---

### P0-4 补索引

**问题**：`orders.user_id` 没有索引，查某人的订单要全表扫。

**做法**：新增迁移 `0005_add_indexes`

```sql
CREATE INDEX idx_orders_user_id ON orders (user_id);
CREATE INDEX idx_users_deleted_id ON users (is_deleted, id);
```

**验收**：`EXPLAIN` 从 `type=ALL` 变成 `type=ref`。

**工作量**：1 小时

---

### P0-5 转账并发修复

**问题**：读出来改属性，并发会丢更新（代码里自己标了 ⚠️）。

**做法**：改成原子 SQL。

```python
# 扣款：余额够才扣，靠影响行数判断
result = db.execute(
    update(User)
    .where(User.id == from_id, User.balance >= amount)
    .values(balance=User.balance - amount)
)
if result.rowcount == 0:
    raise AppError("余额不足")

# 加款
db.execute(update(User).where(User.id == to_id).values(balance=User.balance + amount))
db.commit()
```

**验收**：并发 10 个线程同时转账，总金额不变。

**工作量**：3 小时（含并发测试）

---

### P0-6 软删与唯一索引冲突

**问题**：用户被软删后，`username` 仍然占用唯一索引，同名无法再注册。

**做法**（内部系统的简单方案）：删除时给用户名和手机号加后缀。

```python
user.username = f"{user.username}#deleted#{user.id}"
user.phone = f"{user.phone}#deleted#{user.id}"
user.is_deleted = 1
```

**验收**：删除后能注册同名用户。

**工作量**：1 小时

---

### P0-7 日志脱敏

**问题**：日志里可能带手机号、令牌。

**做法**：

- 打印手机号时只留前 3 后 4：`138****0001`
- 令牌只打前 8 位
- 请求体日志里过滤 `password`、`token` 字段

**验收**：抓一遍日志，搜不到完整手机号和完整令牌。

**工作量**：1 小时

---

### P0-8 备份与恢复

**问题**：单机部署，磁盘挂了数据全没。

**做法**：

```bash
# 宿主机 crontab，每天 3 点
docker exec pbn-mysql mysqldump -uroot -p$PASS --single-transaction learn_mysql \
  | gzip > /backup/learn_mysql_$(date +%F).sql.gz

# 保留 7 天
find /backup -name "*.sql.gz" -mtime +7 -delete
```

**关键：必须演练恢复**。没演练过的备份等于没有备份。

```bash
gunzip -c /backup/learn_mysql_2026-11-10.sql.gz | docker exec -i pbn-mysql mysql -uroot -p$PASS learn_mysql
```

**验收**：从备份恢复到一台空库，数据完整。

**工作量**：2 小时（含演练）

---

## 4. P1：上线后第一个月补（4 项）

| 项 | 内容 | 工作量 |
| --- | --- | --- |
| 错误码 | 响应体加 `code` 字段（如 `USER_NOT_FOUND`），前端不用猜 | 2 小时 |
| 审计日志 | 谁改了余额、谁删了用户，单独一张表 | 4 小时 |
| 基础指标 | `/metrics` 暴露 QPS、延迟、连接池用量 | 3 小时 |
| Nginx + HTTPS | 反代、证书、`client_max_body_size 1m` | 2 小时 |

---

## 5. 上线检查清单

上线前逐项打勾，**任何一项没打勾就不上线**：

```plain
[ ] ENV=prod 时，密钥缺失会让启动失败
[ ] JWT_SECRET 是随机生成的、>=32 字节、存在密钥管理里
[ ] MYSQL_PASSWORD / REDIS_PASSWORD 非空
[ ] CORS 白名单配置的是真实前端域名
[ ] 登录失败 5 次返回 429
[ ] EXPLAIN 确认 orders.user_id / users(is_deleted,id) 走了索引
[ ] 并发转账测试通过（总额守恒）
[ ] 软删后能注册同名用户
[ ] 日志里搜不到完整手机号和完整令牌
[ ] 备份任务已配，且演练恢复成功
[ ] 数据库端口不对公网暴露（只开 80/443）
[ ] 容器 restart 策略是 unless-stopped 或 always
[ ] 磁盘使用率有监控（或至少每周看一眼）
[ ] 有一份"出事了怎么办"的文档
```

---

## 6. 运维手册要点

内部系统的运维不需要复杂平台，但这几件事要写下来：

| 场景 | 怎么做 |
| --- | --- |
| 服务挂了 | `docker compose ps` → `docker compose logs app --tail 100` |
| 要发布新版本 | `docker compose up -d --build app`（只重建应用） |
| 要回滚 | 保留上一个镜像 tag：`docker tag` 后再 `compose up` 指定 tag |
| 数据库要迁移 | **先备份**，再 `alembic upgrade head` |
| 磁盘满了 | 清 `/var/lib/docker` 的旧镜像、清备份、查日志大小 |
| 用户报障 | 让他提供页面上的 `X-Request-ID`，按 id 搜日志 |

---

## 7. 时间表

| 周 | 内容 | 产出 |
| --- | --- | --- |
| 第 1 周 | P0-1 ~ P0-5（配置、CORS、限流、索引、转账） | 能安全上线 |
| 第 2 周 | P0-6 ~ P0-8（软删、脱敏、备份）+ 上线清单逐项验证 | 能稳定运行 |
| 第 3 周 | 部署到服务器、配 Nginx、跑通全流程 | 正式上线 |
| 第 4 周 | P1（错误码、审计、指标、HTTPS） | 可运维 |

**总计约 4 周**（每天 3~4 小时）。

---

## 8. 风险提示

| 风险 | 说明 | 缓解 |
| --- | --- | --- |
| 单点故障 | 一台机器，挂了就全停 | 每日备份 + 快速重建脚本 + 接受几小时停机 |
| 数据丢失 | 备份没演练过 | P0-8 强制演练 |
| 密钥泄露 | .env 被误提交 | `.gitignore` + `.dockerignore` + 上线前 `git log -p` 搜一遍 |
| 迁移锁表 | 大表加索引会锁 | 内部系统数据量小，可接受；但要在低峰期做 |

---

## 9. 一条重要的心态

> **生产级的核心不是"技术多先进"，是"出事时你兜得住"。**
>
> 内部系统用单机 + 每日备份 + 清晰的日志，比用 K8s 却没有备份强一百倍。
