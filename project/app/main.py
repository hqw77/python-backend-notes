"""应用入口.启动方式:uvicorn app.main:app --reload"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.exceptions import AppError
from app.core.middleware import register_middlewares
from app.db.engine import engine
from app.db.redis_client import close_redis
from app.routers import auth, health, users, wallet


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动:以后在这里做连接池预热,缓存加载
    yield
    # 关闭:释放 MySQL 连接池和 Redis 连接,避免进程退出时连接悬空
    engine.dispose()
    close_redis()


setup_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    lifespan=lifespan,
)

# 请求 id + 耗时统计, 在注册路由之前挂上
register_middlewares(app)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(wallet.router)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """把业务异常统一映射成 {"detail": "..."} + 对应的状态码."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
