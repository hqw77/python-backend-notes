"""Redis 连接池.

和 MySQL 的 engine 一个道理: 连接池全进程只建一次, 各处在用的时候借用.
decode_responses=True 让取出来的值直接是 str, 不用手动 decode.
"""

import redis

from app.core.config import settings

# 连接池: 进程内共享
redis_pool = redis.ConnectionPool(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db,
    password=settings.redis_password or None,
    decode_responses=True,
    max_connections=settings.redis_max_connections,
)

# 客户端: 每次操作都用它, 它内部从池子里借连接
redis_client = redis.Redis(connection_pool=redis_pool)


def close_redis() -> None:
    """进程退出时释放所有连接, 由 lifespan 调用."""
    redis_pool.disconnect()
