"""OpenAPI 契约的测试.

验证错误响应真的写进了文档 - 这是"文档不骗人"的自动化保障.
"""


def _spec(client) -> dict:
    return client.get("/openapi.json").json()


def test_error_schema_registered(client):
    """ErrorResponse 要出现在组件的 schemas 里."""
    schemas = _spec(client)["components"]["schemas"]
    assert "ErrorResponse" in schemas
    assert "detail" in schemas["ErrorResponse"]["properties"]


def test_user_detail_declares_404(client):
    """用户详情接口要声明 404."""
    responses = _spec(client)["paths"]["/users/{user_id}"]["get"]["responses"]
    assert "404" in responses
    ref = responses["404"]["content"]["application/json"]["schema"]["$ref"]
    assert ref.endswith("ErrorResponse")


def test_create_user_declares_409(client):
    """创建用户要声明 409(用户名重复)."""
    responses = _spec(client)["paths"]["/users"]["post"]["responses"]
    assert "409" in responses


def test_login_declares_401(client):
    """登录要声明 401(密码错误)."""
    responses = _spec(client)["paths"]["/auth/login"]["post"]["responses"]
    assert "401" in responses


def test_error_response_matches_schema(client):
    """真实返回要和声明的 schema 一致: 都是 {detail: ...}."""
    r = client.get("/users/99999999")
    assert r.status_code == 404
    body = r.json()
    assert set(body) == {"detail"}
    assert isinstance(body["detail"], str)
