"""分页接口的测试.

验证两件事:
    1. 分页参数生效(page/size)
    2. 非法参数被 Query 的校验规则挡下(422)
"""


def test_list_users_default_page(client):
    """默认第 1 页, 每页 10 条."""
    r = client.get("/users")
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 1
    assert body["size"] == 10
    assert len(body["items"]) <= 10


def test_list_users_custom_page(client):
    """指定 page 与 size, 返回的分页信息要一致."""
    r = client.get("/users?page=2&size=2")
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 2
    assert body["size"] == 2
    assert len(body["items"]) <= 2


def test_list_users_invalid_size(client):
    """size 超过上限返回 422, 这是 PageParams 里 Query(le=100) 的作用."""
    r = client.get("/users?size=999")
    assert r.status_code == 422


def test_list_users_invalid_page(client):
    """page 小于 1 返回 422."""
    r = client.get("/users?page=0")
    assert r.status_code == 422


def test_sort_by_balance(client):
    """sort=balance 时按余额升序返回."""
    r = client.get("/users?sort=balance&size=100")
    assert r.status_code == 200
    balances = [float(u["balance"]) for u in r.json()["items"]]
    assert balances == sorted(balances)


def test_sort_by_balance_desc(client):
    """sort=-balance 时按余额降序返回."""
    r = client.get("/users?sort=-balance&size=100")
    assert r.status_code == 200
    balances = [float(u["balance"]) for u in r.json()["items"]]
    assert balances == sorted(balances, reverse=True)


def test_sort_invalid_field(client):
    """排序字段不在白名单里返回 422, 这是在入口挡住的."""
    r = client.get("/users?sort=password_hash")
    assert r.status_code == 422
