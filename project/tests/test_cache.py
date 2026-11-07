"""Redis 缓存相关的测试.

运行:
    cd project
    ..\\.venv\\Scripts\\python.exe -m pytest tests -q
"""

from app.db.redis_client import redis_client
from app.services import cache


def test_detail_creates_cache(client, temp_user):
    """第一次查详情会写缓存, 并且带 TTL."""
    key = cache.user_key(temp_user["id"])
    redis_client.delete(key)

    r = client.get(f"/users/{temp_user['id']}")
    assert r.status_code == 200
    assert redis_client.exists(key) == 1
    assert redis_client.ttl(key) > 0


def test_detail_hits_cache(client, temp_user):
    """第二次查命中缓存: 改掉缓存里的值, 接口返回的也跟着变."""
    key = cache.user_key(temp_user["id"])
    client.get(f"/users/{temp_user['id']}")          # 先让缓存写进去

    fake = cache.get_json(key)
    fake["username"] = "缓存里的名字"
    cache.set_json(key, fake)                        # 篡改缓存

    r = client.get(f"/users/{temp_user['id']}")
    assert r.json()["username"] == "缓存里的名字"     # 说明读的是缓存, 不是库

    redis_client.delete(key)


def test_update_balance_invalidates(client, temp_user):
    """改余额后缓存应该被删掉."""
    key = cache.user_key(temp_user["id"])
    client.get(f"/users/{temp_user['id']}")
    assert redis_client.exists(key) == 1

    r = client.put(f"/users/{temp_user['id']}/balance", json={"amount": "10.00"})
    assert r.status_code == 200
    assert redis_client.exists(key) == 0


def test_soft_delete_invalidates(client, temp_user):
    """软删除后缓存也失效."""
    key = cache.user_key(temp_user["id"])
    client.get(f"/users/{temp_user['id']}")

    r = client.delete(f"/users/{temp_user['id']}")
    assert r.status_code == 204
    assert redis_client.exists(key) == 0


def test_404_is_not_cached(client):
    """查不存在的用户返回 404, 并且不会写入缓存."""
    key = "user:99999999"
    redis_client.delete(key)

    r = client.get("/users/99999999")
    assert r.status_code == 404
    assert redis_client.exists(key) == 0
