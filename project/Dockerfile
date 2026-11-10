# syntax=docker/dockerfile:1

# ---------- 阶段一: 装依赖 ----------
# 单独用一个阶段装依赖, 好处是: 依赖不变时这一层能命中缓存,
# 改代码不会重新装一遍包.
FROM python:3.12-slim AS builder

WORKDIR /app

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt


# ---------- 阶段二: 运行时 ----------
# 只带装好的包和源码, 不带编译器、缓存, 镜像小很多.
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# 用非 root 用户跑应用, 万一被攻破影响面更小
RUN useradd --create-home --shell /bin/bash appuser

COPY --from=builder /install /usr/local
COPY . .

USER appuser

EXPOSE 8000

# 容器健康检查: 直接请求 /health, 失败就标记 unhealthy
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status == 200 else 1)"

# 注意没有 --reload: 生产环境不需要热重载
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
