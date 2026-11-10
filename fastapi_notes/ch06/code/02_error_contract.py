"""FastAPI 第二部分 - 案例 6-2: 把错误响应写进文档(契约).

上一条案例发现: 代码里 raise 的 404, 文档里看不到.
前端照着文档写代码, 就不会处理这个错误, 上线才发现有 404.

解决办法: 定义一个统一的错误模型, 在装饰器里声明 responses.

怎么跑:
    python fastapi_notes/ch06/code/02_error_contract.py
"""

import json
import warnings

warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402


class ErrorResponse(BaseModel):
    """全项目统一的错误格式."""

    detail: str = Field(description="错误说明")


class ItemOut(BaseModel):
    id: int
    name: str


app = FastAPI(title="错误契约演示")


@app.get(
    "/items/{item_id}",
    response_model=ItemOut,
    summary="商品详情",
    responses={
        404: {"model": ErrorResponse, "description": "商品不存在"},
        409: {"model": ErrorResponse, "description": "数据冲突"},
    },
)
def get_item(item_id: int):
    if item_id > 100:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"id": item_id, "name": f"商品{item_id}"}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    spec = app.openapi()

    show("① 现在文档里能看到 404 了")
    responses = spec["paths"]["/items/{item_id}"]["get"]["responses"]
    for code, detail in responses.items():
        model = detail.get("content", {}).get("application/json", {}).get("schema", {})
        print(f"    {code}: {detail.get('description', ''):12} schema={model}")

    show("② 声明的错误格式必须和真实返回一致")
    with TestClient(app) as client:
        r = client.get("/items/999")
        print("    真实返回:", r.status_code, r.json())
    print("    → {detail: ...} 和 ErrorResponse 对上了, 契约没撒谎")

    show("③ 如果两者不一致会怎样")
    print("    文档写 {detail: str}, 实际返回 {msg: str}")
    print("    前端按文档写 r.data.detail, 永远拿到 undefined")
    print("    → 这种'文档骗人'比没文档更糟")

    show("④ 为什么值得做")
    print("    前端不用猜错误格式, 直接按 schema 生成类型")
    print("    接口联调时少一轮'这个 404 返回什么'的沟通")
    print("    /docs 页面里能点到具体的错误示例")

    show("⑤ 完整契约还差什么")
    print("    统一的错误码(不只是 HTTP 状态码)")
    print("    错误分类(business / validation / system)")
    print("    这些属于业务约定, 可以用 ErrorResponse 加字段扩展")
    print("    例: {'code': 'USER_NOT_FOUND', 'detail': '...'}")
