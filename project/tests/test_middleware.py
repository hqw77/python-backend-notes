"""中间件的测试: 请求 id 与耗时响应头."""

from app.core.middleware import PROCESS_TIME_HEADER, REQUEST_ID_HEADER


def test_response_has_request_id(client):
    """每个响应都要带 X-Request-ID."""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.headers.get(REQUEST_ID_HEADER)
    assert len(r.headers[REQUEST_ID_HEADER]) == 12


def test_request_id_is_passed_through(client):
    """客户端带了 id 就复用客户端的, 不乱改."""
    r = client.get("/health", headers={REQUEST_ID_HEADER: "client-id-001"})
    assert r.headers[REQUEST_ID_HEADER] == "client-id-001"


def test_request_id_is_unique_per_request(client):
    """两次请求生成的 id 不同."""
    a = client.get("/health").headers[REQUEST_ID_HEADER]
    b = client.get("/health").headers[REQUEST_ID_HEADER]
    assert a != b


def test_response_has_process_time(client):
    """响应头带耗时, 格式类似 12.3ms."""
    r = client.get("/health")
    value = r.headers.get(PROCESS_TIME_HEADER)
    assert value is not None
    assert value.endswith("ms")


def test_request_id_available_in_route(client, temp_user):
    """request.state 里的 id 能被路由/依赖读取.

    这里用 /users/{id} 验证: 中间件已经执行过, 接口仍能正常返回.
    """
    r = client.get(f"/users/{temp_user['id']}")
    assert r.status_code == 200
    assert r.headers.get(REQUEST_ID_HEADER)
