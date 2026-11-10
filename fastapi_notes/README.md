# 第二部分 · FastAPI 深入

> 状态:**进行中（ch01~ch03 已完成）**
> 第一部分 `mysql_notes/` 里的第六章、第七章已经把 FastAPI 的基础用过了(路由、校验、依赖注入、状态码、异常映射)。这里放的是"用得上但基础篇没讲透"的部分。

## 计划内容

| 章 | 主题 | 说明 | 状态 |
| --- | --- | --- | --- |
| [ch01](ch01/notes/依赖注入进阶.md) | 依赖注入进阶 | `Depends` 的缓存机制、子依赖、类作为依赖、`yield` 依赖的清理时机 | ✅ 完成 |
| [ch02](ch02/notes/中间件与请求生命周期.md) | 中间件与请求生命周期 | 请求 id 透传、耗时统计、CORS、中间件顺序与异常坑 | ✅ 完成 |
| [ch03](ch03/notes/后台任务与异步.md) | 后台任务与异步 | `async def` vs `def`、事件循环阻塞、`BackgroundTasks`、何时上 Celery | ✅ 完成 |
| ch04 | 分层再设计 | 把 service 的返回值从 ORM 对象换成 DTO;分页/排序的统一封装 | ⬜ 待开始 |
| ch05 | 可观测性 | 结构化日志、慢请求告警、错误上报 | ⬜ 待开始 |
| ch06 | 文档与契约 | OpenAPI 定制、错误响应统一声明、客户端 SDK 生成 | ⬜ 待开始 |
| ch07 | 测试进阶 | 依赖覆盖(`dependency_overrides`)、测试库隔离、异步测试 | ⬜ 待开始 |

## 案例清单

| 文件 | 验证什么 |
| --- | --- |
| `ch01/code/01_depends_basic.py` | `Depends` 的基本用法、参数自动提升与校验 |
| `ch01/code/02_depends_cache.py` | 依赖缓存:一个请求只执行一次,`use_cache=False` 的差别 |
| `ch01/code/03_sub_dependency.py` | 子依赖:令牌 → 用户 → 角色的三层依赖链 |
| `ch01/code/04_class_and_yield.py` | 类作为依赖、`yield` 依赖的清理时机(含异常路径) |
| `ch02/code/01_middleware_basic.py` | 中间件的进入/返回顺序, 异常时后半段不执行 |
| `ch02/code/02_request_id.py` | 请求 id 的生成、透传与回写响应头 |
| `ch02/code/03_timing.py` | 耗时统计与慢请求告警, perf_counter 的用法 |
| `ch02/code/04_cors.py` | 预检请求、白名单、浏览器同源策略 |
| `ch02/code/05_order_and_pitfall.py` | 洋葱顺序 + 中间件异常不被 exception_handler 捕获 |
| `ch03/code/01_blocking_event_loop.py` | async def 里 time.sleep 拖慢 5 倍 |
| `ch03/code/02_def_in_threadpool.py` | 同一个阻塞函数, def 比 async def 快 5 倍 |
| `ch03/code/03_background_tasks.py` | 后台任务把 0.3 秒等待挪到响应之后, 异常被吞 |

运行方式(在仓库根目录):

```bash
python fastapi_notes/ch01/code/01_depends_basic.py
python fastapi_notes/ch01/code/04_class_and_yield.py
```

所有案例都是自带小应用的独立脚本,不依赖 `project/`,可以反复运行。

## 目录规范

与 `mysql_notes/` 保持一致:

```plain
fastapi_notes/
├── README.md
├── chNN/
│   ├── notes/        # 笔记(教材骨架 + 通俗理解注解 + 案例引用)
│   └── code/         # 可运行案例,编号 NN_xxx.py
└── extras/notes/     # 番外
```

笔记格式见 [DOC-PATTERN](../docs/DOC-PATTERN.md)。

## 与工程的关系

新增能力应落到 `project/`,不是只写 demo:

- 中间件 → `project/app/main.py`
- 依赖覆盖 → `project/tests/conftest.py`
- 日志 → `project/app/core/logging.py`

## 前置

- 完成 `mysql_notes/` 第六、七章
- `project/` 能启动、测试全绿
