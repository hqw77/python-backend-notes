# python-backend-notes

[![CI](https://github.com/hqw77/python-backend-notes/actions/workflows/ci.yml/badge.svg)](https://github.com/hqw77/python-backend-notes/actions/workflows/ci.yml)

从写第一句 `SELECT` 开始,一路走到 **FastAPI 分层应用 + Redis 缓存 + Docker 部署**的后端学习仓库。

每一章都留下三样东西：**可运行的代码**、**能复现的实测数据**、**自己整理过的笔记**。

---

## 这个仓库是什么

它同时是三种东西：

| 身份 | 对谁有用 | 体现 |
| --- | --- | --- |
| **学习笔记** | 自己复习 | 19 章 / 26 篇笔记 / 9200 行 |
| **作品集** | 面试时展示 | 13 个接口 / 45 个测试 / CI 绿标 / 一条命令可跑 |
| **可上线骨架** | 内部系统 | 分层、认证、缓存、日志、迁移全齐 |

### 硬指标

| 项 | 数量 |
| --- | --- |
| 教程章节 | **19 章**（MySQL 8 · Redis 3 · FastAPI 7 · Docker 1） |
| 笔记 | 26 篇 / 约 9200 行 |
| 可运行案例 | **55 个** / 约 4600 行 |
| 应用代码 | 1300 行 / 26 文件 |
| 测试 | **45 个** / 551 行,CI 全绿 |
| 接口 | 13 个 |
| 数据表 | 4 张(`users` / `orders` / `roles` / `user_roles`) |
| 数据库迁移 | 4 个版本 |

---

## 30 秒跑起来

### 方式一：Docker(推荐,不用装任何东西)

```bash
git clone https://github.com/hqw77/python-backend-notes.git
cd python-backend-notes/project
docker compose up -d --build
```

打开 <http://127.0.0.1:8000/docs>。

启动时会自动跑迁移(`alembic upgrade head`),**空库也能直接起来**。

```plain
NAME        STATUS                    PORTS
pbn-app     Up (healthy)              0.0.0.0:8000->8000/tcp
pbn-mysql   Up (healthy)              0.0.0.0:3307->3306/tcp
pbn-redis   Up (healthy)              0.0.0.0:6380->6379/tcp
```

> 宿主机端口错开了本机的 MySQL(3306) 和 Redis(6379)。

### 方式二:本地跑(改代码时用)

```bash
python -m venv .venv
source .venv/Scripts/activate                    # PowerShell: .venv\Scripts\Activate.ps1
pip install -r project/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

cd project
cp .env.example .env                             # 填数据库密码
alembic upgrade head                             # 建表
uvicorn app.main:app --reload
```

| 地址 | 说明 |
| --- | --- |
| `/docs` | Swagger 接口文档 |
| `/health` | 进程存活(不碰数据库) |
| `/health/db` | 数据库连通(返回 MySQL 版本) |

---

## 目录结构

```plain
python-backend-notes/
├── mysql_notes/              # 第一部分：MySQL + ORM + Web（8 章）
│   ├── README.md             # 这部分的总纲
│   ├── ch01/                 # SQL 基础：建表 / JOIN / 事务 / 索引 / 设计 / 运维
│   │   ├── notes/            #   阶段 0 ~ 阶段 7（8 篇）
│   │   ├── code/             #   phase0 ~ phase6（8 个脚本）
│   │   └── sql/              #   10 个 SQL 脚本
│   ├── ch02/                 # 连接池：原理 + PooledDB + 压测
│   ├── ch03/                 # SQLAlchemy ORM 基础
│   ├── ch04/                 # SQLAlchemy CRUD
│   ├── ch05/                 # 关系映射 / N+1 / 并发
│   ├── ch06/                 # FastAPI 与 MySQL 接口
│   ├── ch07/                 # 完整项目实战：认证 / 权限 / 事务 / 测试
│   ├── ch08/                 # 面试题与项目复盘
│   └── extras/notes/         # 番外 01：Alembic 数据库迁移
├── redis_notes/              # 第二部分：Redis（3 章）
│   ├── ch01/                 # Redis 基础：五种类型、过期、Python 操作
│   ├── ch02/                 # 缓存设计：Cache-Aside、穿透/击穿/雪崩、一致性
│   ├── ch03/                 # 接入 project/：缓存服务、失效、测试
│   └── README.md
├── fastapi_notes/            # 第三部分：FastAPI 深入（7 章）
│   ├── ch01/                 # 依赖注入进阶
│   ├── ch02/                 # 中间件与请求生命周期
│   ├── ch03/                 # 后台任务与异步
│   ├── ch04/                 # 分层再设计（ORM vs DTO）
│   ├── ch05/                 # 可观测性（日志 + request_id）
│   ├── ch06/                 # 文档与契约（OpenAPI）
│   ├── ch07/                 # 测试进阶
│   └── README.md
├── docker_notes/             # 第四部分：Docker 与部署（1 章）
│   ├── ch01/                 # 容器与编排入门
│   └── README.md
├── project/                  # 四部分共用的工程产物
│   ├── app/                  # 应用代码
│   ├── tests/                # 45 个 pytest 用例
│   ├── migrations/           # Alembic 迁移（0001 ~ 0004）
│   ├── Dockerfile            # 多阶段构建
│   ├── docker-compose.yml    # mysql + redis + app
│   └── README.md             # 工程说明：接口清单、配置项、设计
├── docs/                     # 架构 / 规划 / 规范 / 代码导读 / 生产化方案
└── README.md
```

**四个 `*_notes/` 是学习线,`project/` 是它们共同的产物。**

章节案例通过 `sys.path` 引用 `project/app`,但工程本身**不依赖**任何笔记目录——可以单独拷出去部署。

---

## 学习路线

按顺序读,每一部分都建立在前一部分之上。

### 第一部分 · MySQL + ORM + Web(`mysql_notes/`,8 章)

> 从 SQL 到能跑的用户 API。这一部分是整个仓库的地基。

| 章 | 主题 | 笔记 |
| --- | --- | --- |
| 1 | MySQL 进阶基础:建表规范、JOIN、事务、索引、设计、运维 | [8 篇阶段笔记](mysql_notes/ch01/notes/) |
| 2 | Python 数据库连接池:建连代价、PooledDB、压测(4.3 倍) | [第二章](mysql_notes/ch02/notes/Python%20数据库连接池.md) |
| 3 | SQLAlchemy ORM 基础:Engine / Base / Model / Session、脏检查 | [第三章](mysql_notes/ch03/notes/SQLAlchemy%20ORM%20基础.md) |
| 4 | ORM CRUD:分页、批量、软删、service 分层 | [第四章](mysql_notes/ch04/notes/SQLAlchemy%20ORM%20CRUD.md) |
| 5 | 关系映射:一对多、多对多、N+1、并发丢更新 | [第五章](mysql_notes/ch05/notes/SQLAlchemy%20进阶.md) |
| 6 | FastAPI + MySQL:schema、状态码、异常映射、TestClient | [第六章](mysql_notes/ch06/notes/FastAPI%20+%20MySQL.md) |
| 7 | 完整项目实战:argon2、JWT、RBAC、转账事务、pytest | [第七章](mysql_notes/ch07/notes/完整项目实战.md) |
| 8 | 面试题与项目复盘:12 道题、踩坑记录、简历写法 | [第八章](mysql_notes/ch08/notes/面试题与项目复盘.md) |
| 番外 | Alembic:为什么不用 `create_all`、基线、`include_object` 防误删 | [番外 01](mysql_notes/extras/notes/01-Alembic%20数据库迁移.md) |

### 第二部分 · Redis(`redis_notes/`,3 章)

> 数据不能只压在 MySQL 上。这部分讲缓存怎么加、加了会出什么事。

| 章 | 主题 | 笔记 |
| --- | --- | --- |
| 1 | Redis 基础:五种类型 + 48 条命令表、过期、key 命名 | [第一章](redis_notes/ch01/notes/Redis%20基础.md) |
| 2 | 缓存设计:Cache-Aside、穿透/击穿/雪崩、一致性 | [第二章](redis_notes/ch02/notes/缓存设计与三大问题.md) |
| 3 | 接入工程:DTO 缓存、写操作失效、5 个缓存测试 | [第三章](redis_notes/ch03/notes/把缓存接进项目.md) |

### 第三部分 · FastAPI 深入(`fastapi_notes/`,7 章)

> 基础篇讲"怎么用",这部分讲"用错会怎样"。

| 章 | 主题 | 笔记 |
| --- | --- | --- |
| 1 | 依赖注入进阶:依赖缓存、子依赖、类依赖、`yield` 清理 | [第一章](fastapi_notes/ch01/notes/依赖注入进阶.md) |
| 2 | 中间件:请求 id、耗时、CORS、洋葱顺序、异常坑 | [第二章](fastapi_notes/ch02/notes/中间件与请求生命周期.md) |
| 3 | 后台任务与异步:`async def` vs `def`、事件循环阻塞 | [第三章](fastapi_notes/ch03/notes/后台任务与异步.md) |
| 4 | 分层再设计:ORM vs DTO、`DetachedInstanceError`、排序白名单 | [第四章](fastapi_notes/ch04/notes/分层再设计.md) |
| 5 | 可观测性:日志格式、`contextvar` 传 request_id | [第五章](fastapi_notes/ch05/notes/可观测性.md) |
| 6 | 文档与契约:OpenAPI 来源、`responses` 声明错误、契约测试 | [第六章](fastapi_notes/ch06/notes/文档与契约.md) |
| 7 | 测试进阶:依赖覆盖、事务隔离、`parametrize` | [第七章](fastapi_notes/ch07/notes/测试进阶.md) |

### 第四部分 · Docker(`docker_notes/`,1 章)

> 让别人一条命令跑起来。Docker 是工具,讲透一次就够。

| 章 | 主题 | 笔记 |
| --- | --- | --- |
| 1 | 镜像与容器、Dockerfile 逐指令、多阶段构建、compose 编排 | [第一章](docker_notes/ch01/notes/容器与编排入门.md) |

---

## 工程:`project/`

### 接口清单(13 个)

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/health` | 公开 | 进程存活 |
| GET | `/health/db` | 公开 | 数据库连通 |
| POST | `/auth/register` | 公开 | 注册(响应后异步发通知) |
| POST | `/auth/login` | 公开 | 登录,返回 JWT |
| GET | `/auth/me` | 登录 | 当前用户与角色 |
| GET | `/users` | 公开 | 分页 + 排序(6 种白名单值) |
| GET | `/users/{id}` | 公开 | 详情(**带缓存**,命中时 0 条 SQL) |
| POST | `/users` | 公开 | 创建 |
| PUT | `/users/{id}/balance` | 公开 | 调整余额 |
| DELETE | `/users/{id}` | 公开 | 软删除 |
| GET | `/users/{id}/roles` | 公开 | 查询角色 |
| POST | `/users/{id}/roles` | **admin** | 分配角色 |
| POST | `/transfer` | 登录 | 转账(单事务) |

### 分层

依赖方向单向：`routers → services → models`。反向依赖视为设计错误。

| 层 | 只负责 | 禁止 |
| --- | --- | --- |
| `routers/` | 入参出参、状态码、依赖注入 | 写 SQL、写业务规则 |
| `services/` | 业务规则、事务边界、抛业务异常 | 感知 HTTP |
| `models/` | 表结构映射与关系 | 业务判断 |
| `db/` | Engine / Session / Redis 生命周期 | 业务代码 |
| `core/` | 配置、安全、日志、中间件、异常 | 依赖上层 |

**验证方法**:在 `routers/` 目录下搜 `select(` 和 `commit`,应该是 0 处。

### 技术栈

| 组件 | 用途 |
| --- | --- |
| FastAPI + uvicorn | Web 框架与 ASGI 服务器 |
| SQLAlchemy 2.1 + PyMySQL | ORM 与驱动 |
| Alembic | 表结构版本控制(4 个迁移) |
| Pydantic v2 | 请求响应模型与校验 |
| argon2-cffi | 密码哈希 |
| PyJWT | 令牌签发校验 |
| redis-py | 缓存(Cache-Aside) |
| pytest + httpx | 45 个接口测试 |
| Docker + Compose | 一键部署 |

---

## 实测数据

这个仓库的每个技术结论都跑过,数字可复现。

| 场景 | 结果 | 出自 |
| --- | --- | --- |
| 缓存效果 | **0.34 ms/次 vs 50.4 ms/次**,差约 150 倍 | [redis ch02](redis_notes/ch02/notes/缓存设计与三大问题.md) |
| N+1 查询 | 懒加载 4 条 SQL → `selectinload` **2 条** | [mysql ch05](mysql_notes/ch05/notes/SQLAlchemy%20进阶.md) |
| 连接池 | 11.40 ms vs 2.66 ms,**4.3 倍** | [mysql ch02](mysql_notes/ch02/notes/Python%20数据库连接池.md) |
| 批量写入 | 100 条:**0.185 s → 0.014 s**(12.9 倍) | [mysql ch04](mysql_notes/ch04/notes/SQLAlchemy%20ORM%20CRUD.md) |
| 异步阻塞 | 5 并发:`async def` + `time.sleep` **1.51 s**,`await asyncio.sleep` **0.31 s** | [fastapi ch03](fastapi_notes/ch03/notes/后台任务与异步.md) |
| 缓存穿透 | 压库 **100 次 → 1 次**(空值缓存) | [redis ch02](redis_notes/ch02/notes/缓存设计与三大问题.md) |
| 缓存击穿 | 压库 **10 次 → 1 次**(互斥锁) | 同上 |
| 详情接口 | 命中缓存后发 **0 条 SELECT** | [redis ch03](redis_notes/ch03/notes/把缓存接进项目.md) |

---

## 质量保障

### 测试分布(45 个)

| 文件 | 数量 | 测什么 |
| --- | --- | --- |
| `test_auth.py` | 8 | 注册、登录、令牌、401/403 |
| `test_cache.py` | 5 | 缓存命中、写操作失效、404 不缓存 |
| `test_pagination.py` | 7 | 分页参数、排序白名单、非法值 422 |
| `test_middleware.py` | 5 | `X-Request-ID`、`X-Process-Time` |
| `test_background.py` | 2 | 后台通知被触发、接口行为不变 |
| `test_openapi.py` | 5 | 错误契约声明与真实返回一致 |
| `test_overrides.py` | 2 | 依赖覆盖与清理 |
| `test_validation.py` | 9 | 参数化覆盖各类非法输入 |
| `test_schema.py` | 2 | 模型与表齐全、迁移版本存在 |

### CI

每次 push 自动跑:

```plain
起 MySQL 8.0 + Redis 7(service containers)
  → 装依赖 → compileall 语法检查
  → alembic upgrade head
  → pytest(45 个)
  → alembic check(确认模型与库无漂移)
```

> CI 第一次运行就抓出一个真 bug:`orders` 表从来没进过迁移。本地因为手工建过所以没事,全新库直接报错。这就是 CI 的价值。

### 编码约定

| 规则 | 说明 |
| --- | --- |
| 代码严格英文标点 | `.py` / `.sql` 里 0 个中文标点 |
| 文档保留中文标点 | 只有逗号统一用英文 `,` |
| 目录名不与包同名 | 用 `*_notes`,避免遮蔽 `import redis` |
| 每章笔记与代码分开放 | `notes/` 只放 `.md`,`code/` 只放 `.py` |

完整规范见 [docs/DOC-PATTERN.md](docs/DOC-PATTERN.md)。

---

## 文档地图

| 文件 | 给谁看 | 内容 |
| --- | --- | --- |
| [README.md](README.md) | 逛仓库的人 | 就是这一页 |
| [project/README.md](project/README.md) | 想跑项目的人 | 接口、配置项、认证流程、设计说明 |
| [docs/CODE-READING.md](docs/CODE-READING.md) | 想读代码的人 | 按请求链路分 7 站,每站附答案 |
| [docs/DOC-PATTERN.md](docs/DOC-PATTERN.md) | 想写新章节的人 | 文档模板与写作规则 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | 想理解设计的人 | 分层、依赖方向、完成度矩阵 |
| [docs/COURSE-PLAN.md](docs/COURSE-PLAN.md) | 想知道规划的人 | 各章目标与进度 |
| [docs/PRODUCTION-PLAN.md](docs/PRODUCTION-PLAN.md) | 真要上线的人 | 生产化 P0/P1 清单(内部系统 · 单机) |

---

## 数据库迁移

表结构变更一律走 Alembic,不要用 `Base.metadata.create_all`。

```bash
cd project                               # alembic.ini 在 project/ 下
alembic current                          # 当前版本(应为 0004_orders)
alembic check                            # 模型与库是否有差异
alembic revision --autogenerate -m "说明" # 生成迁移
alembic upgrade head                     # 应用
alembic downgrade -1                     # 回退一步
```

> 库里有第一章遗留的练习表(`students`/`books`/`big_users`…),它们没有 ORM 模型。
> `migrations/env.py` 里的 `include_object` 会排除这些表,防止 autogenerate 生成 `DROP TABLE`。

---

## 常见问题

| 现象 | 原因 / 解决 |
| --- | --- |
| `mysql: command not found` | PATH 没生效,重启 VSCode 让新环境变量生效 |
| `detected dubious ownership` | `git config --global --add safe.directory 仓库路径` |
| `pip install` 卡住 | 加 `-i https://pypi.tuna.tsinghua.edu.cn/simple` |
| `ModuleNotFoundError: No module named 'app'` | 没在 `project/` 下启动,或没激活 venv |
| `redis.exceptions.ConnectionError` | Redis 没启动:`docker start mysql-learn-redis` |
| `Table 'xxx' doesn't exist` | 没跑迁移:`cd project && alembic upgrade head` |
| `port is already allocated` | 宿主机端口被占,改 compose 里的映射 |
| 改了代码 Docker 没生效 | 用旧镜像了:`docker compose up -d --build` |

---

## 进度与下一步

### 已完成

```plain
✅ 四部分 19 章教程 + 55 个可运行案例
✅ 13 个接口 + 45 个测试 + CI 绿
✅ Docker 一条命令部署
✅ 4 个数据库迁移,空库可自举
```

### 没做(按优先级)

| # | 事项 | 说明 |
| --- | --- | --- |
| 1 | 生产化 P0 | 限流、密钥管理、备份演练等 8 项,见 [生产化方案](docs/PRODUCTION-PLAN.md) |
| 2 | 第二个项目 | 现在的项目业务偏简单,缺复杂业务场景 |
| 3 | 部署上线 | 还没真跑在服务器上 |

---

<small>仓库从 2026-11-01 开始,当天留下第一条提交。每一条技术结论都有对应提交和可复现的代码。</small>
