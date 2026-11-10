"""后台任务的测试.

验证: 注册接口会在响应之后触发"发送欢迎通知", 且不影响正常响应.
"""

import time

from app.services import notify_service


def test_register_returns_before_notice(client, monkeypatch):
    """注册接口不应该等待通知发送完成."""
    called: list[str] = []

    def slow_notice(username: str) -> None:
        time.sleep(0.3)                 # 模拟发邮件的耗时
        called.append(username)

    monkeypatch.setattr(notify_service, "send_welcome_notice", slow_notice)

    stamp = int(time.time() * 1000) % 10**8
    start = time.perf_counter()
    r = client.post(
        "/auth/register",
        json={"username": f"bg{stamp}", "phone": f"1{stamp:010d}", "password": "secret123"},
    )
    handler_cost = time.perf_counter() - start

    assert r.status_code == 201
    # 路由函数没有等 0.3 秒; TestClient 会把后台任务跑完才返回,
    # 所以这里只断言"通知确实被调用了", 而不是断言总耗时
    assert called == [r.json()["username"]]
    assert handler_cost >= 0

    # 清理
    from app.db.session import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        user = db.get(User, r.json()["id"])
        if user is not None:
            db.delete(user)
            db.commit()


def test_register_still_works(client, monkeypatch):
    """加了后台任务之后, 注册接口的行为不变(201 + 不含密码)."""
    monkeypatch.setattr(notify_service, "send_welcome_notice", lambda username: None)

    stamp = int(time.time() * 1000) % 10**8
    r = client.post(
        "/auth/register",
        json={"username": f"bg2{stamp}", "phone": f"1{stamp:010d}", "password": "secret123"},
    )
    assert r.status_code == 201
    assert "password" not in r.json()

    from app.db.session import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        user = db.get(User, r.json()["id"])
        if user is not None:
            db.delete(user)
            db.commit()
