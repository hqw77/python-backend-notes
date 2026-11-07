"""缓存的读写封装.

这一层只做三件事:
    1. 把 Python 对象转成 JSON 存进去, 取出来再转回来
    2. 统一 key 的命名规则
    3. 统一默认 TTL

业务代码不直接调用 redis_client, 都通过这里, 换缓存实现时只改这一个文件.
"""

import json
from typing import Any

from app.core.config import settings
from app.db.redis_client import redis_client


def user_key(user_id: int) -> str:
    """用户缓存的 key. 全项目只有这一处定义, 避免各处拼错."""
    return f"user:{user_id}"


def get_json(key: str) -> Any | None:
    """读缓存. 命中返回反序列化后的对象, 未命中返回 None."""
    raw = redis_client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


def set_json(key: str, value: Any, ttl: int | None = None) -> None:
    """写缓存. ttl 不传就用配置里的默认值."""
    redis_client.set(
        key,
        json.dumps(value, ensure_ascii=False),
        ex=ttl or settings.redis_default_ttl,
    )


def delete(*keys: str) -> int:
    """删除缓存. 返回真正删掉的个数."""
    if not keys:
        return 0
    return redis_client.delete(*keys)


def exists(key: str) -> bool:
    """判断缓存还在不在, 主要给测试和调试用."""
    return bool(redis_client.exists(key))


def ttl(key: str) -> int:
    """剩余存活秒数. -1 表示永不过期, -2 表示 key 不存在."""
    return redis_client.ttl(key)
