# 第二部分 · FastAPI 深入

> 状态:**进行中（ch01 已完成）**
> 第一部分 `mysql_notes/` 里的第六章、第七章已经把 FastAPI 的基础用过了(路由、校验、依赖注入、状态码、异常映射)。这里放的是"用得上但基础篇没讲透"的部分。

## 计划内容

| 章 | 主题 | 说明 | 状态 |
| --- | --- | --- | --- |
| [ch01](ch01/notes/依赖注入进阶.md) | 依赖注入进阶 | `Depends` 的缓存机制、子依赖、类作为依赖、`yield` 依赖的清理时机 | ✅ 完成 |
| ch02 | 中间件与请求生命周期 | 请求 id、耗时统计、CORS、`BaseHTTPMiddleware` 的坑 | ⬜ 待开始 |
| ch03 | 后台任务与异步 | `BackgroundTasks`、`async def` 与同步阻塞调用的关系、线程池 | ⬜ 待开始 |
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
