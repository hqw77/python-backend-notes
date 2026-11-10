"""用 dependency_overrides 绕过真实依赖的测试.

好处: 不用真的注册 + 登录 + 拿令牌, 直接注入一个"当前用户".
注意: 覆盖之后必须在 finally 里 clear(), 否则会污染后面的测试.
"""

from decimal import Decimal

from app.deps import get_current_user
from app.main import app


class FakeUser:
    """鸭子类型: 只要有路由用到的属性就行, 不必是真的 ORM 对象."""

    id = 999999
    username = "fake-user"
    balance = Decimal("0.00")
    roles: list = []


def test_me_with_overridden_user(client):
    """覆盖 get_current_user 后, 不带令牌也能访问 /auth/me."""
    app.dependency_overrides[get_current_user] = lambda: FakeUser()
    try:
        r = client.get("/auth/me")
        assert r.status_code == 200
        body = r.json()
        assert body["username"] == "fake-user"
        assert body["roles"] == []
    finally:
        app.dependency_overrides.clear()


def test_override_cleared_after_test(client):
    """清空覆盖之后, 接口恢复"要令牌"的行为."""
    r = client.get("/auth/me")
    assert r.status_code == 401
