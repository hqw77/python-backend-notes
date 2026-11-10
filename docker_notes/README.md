# 第四部分 · Docker 与部署

> 状态:**已完成（1 章）**
> 前三部分讲"把代码写好",这部分讲"**让别人一条命令跑起来**"。
> Docker 是工具,不铺成多章:讲透一次就够。

## 为什么单独成一部分

`project/` 现在已经很完整（13 个接口、43 个测试），但别人拿到手仍然要:

```plain
装 Python -> 装 MySQL -> 建库 -> 跑迁移 -> 装依赖 -> 启动
```

**四步里错一步就跑不起来。** 加了容器之后只剩两条命令。

## 章节

| 章 | 主题 | 状态 |
| --- | --- | --- |
| [ch01](ch01/notes/容器与编排入门.md) | 镜像与容器、Dockerfile、多阶段构建、docker compose | ✅ 完成 |

## 案例清单

| 文件 | 验证什么 |
| --- | --- |
| `ch01/code/01_check_env.py` | docker CLI 版本、daemon 是否在跑、镜像与容器列表 |
| `ch01/code/02_container_lifecycle.py` | 镜像 → 容器 → 删除,三者关系 |
| `ch01/code/03_verify_stack.py` | 对已启动的服务做端到端验证(健康检查 + 注册登录 + 缓存) |

运行方式(在仓库根目录):

```bash
python docker_notes/ch01/code/01_check_env.py
```

> 这三个脚本通过 `subprocess` 调 `docker` CLI,需要 Docker Desktop 已启动。
> 连不上时它们会给出提示并跳过,不会抛一堆报错。

## 工程侧的落地

```plain
project/
├── Dockerfile            # 多阶段构建, 非 root 运行, 带 HEALTHCHECK
├── .dockerignore         # 排除 .git / .venv / .env / tests
└── docker-compose.yml    # mysql + redis + app 三个服务
```

一条命令起整套环境:

```bash
cd project
docker compose up -d --build
```

然后打开 http://127.0.0.1:8000/docs。

端口约定（避开本机已有的 MySQL / Redis）:

| 服务 | 宿主机端口 | 容器内端口 |
| --- | --- | --- |
| app | 8000 | 8000 |
| mysql | 3307 | 3306 |
| redis | 6380 | 6379 |

## 目录规范

与其他部分一致:

```plain
docker_notes/
├── README.md
└── chNN/
    ├── notes/        # 笔记(教材骨架 + 通俗理解 + 案例引用)
    └── code/         # 可运行脚本
```

笔记格式见 [DOC-PATTERN](../docs/DOC-PATTERN.md)。

## 下一步

Docker 之后还剩两件事:

1. **CI**: 每次 push 自动跑测试（GitHub Actions）
2. **部署**: 把镜像推到镜像仓库、在一台机器上跑起来

这两件事写成 `docs/` 里的说明即可,不必单独开章。
