"""用 parametrize 覆盖多组边界输入.

同一个测试函数, 跑多组参数 - 比复制粘贴四遍清楚得多.
"""

import pytest


@pytest.mark.parametrize(
    "payload, expected_field",
    [
        ({"username": "a", "phone": "13800000000", "password": "secret123"}, "username"),
        ({"username": "ab", "phone": "123", "password": "secret123"}, "phone"),
        ({"username": "ab", "phone": "23800000000", "password": "secret123"}, "phone"),
        ({"username": "ab", "phone": "13800000000", "password": "123"}, "password"),
    ],
    ids=["username-too-short", "phone-too-short", "phone-not-start-1", "password-too-short"],
)
def test_register_validation(client, payload, expected_field):
    """注册接口的各类非法输入都要返回 422, 且指到具体字段."""
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 422
    fields = [err["loc"][-1] for err in r.json()["detail"]]
    assert expected_field in fields


@pytest.mark.parametrize("balance", ["-1", "-0.01"])
def test_create_user_negative_balance(client, balance):
    """余额不能为负."""
    stamp = abs(hash(balance)) % 10**8
    r = client.post(
        "/users",
        json={"username": f"neg{balance.replace('.', '').replace('-', '')}{stamp}",
              "phone": f"1{stamp:010d}",
              "balance": balance},
    )
    assert r.status_code == 422


@pytest.mark.parametrize("page, size", [(1, 1), (1, 100), (2, 5)])
def test_pagination_valid_ranges(client, page, size):
    """分页参数的合法边界."""
    r = client.get(f"/users?page={page}&size={size}")
    assert r.status_code == 200
    assert r.json()["page"] == page
    assert r.json()["size"] == size
