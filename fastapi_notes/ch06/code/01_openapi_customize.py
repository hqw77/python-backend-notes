"""FastAPI 第二部分 - 案例 6-1: /docs 是怎么生成出来的.

FastAPI 会根据三样东西自动生成 OpenAPI 文档:
    1. 路由的装饰器参数(tags / summary / description / response_model)
    2. 函数的类型注解和 Query/Field 描述
    3. 显式声明的 responses(错误响应)

这个案例建一个小应用, 然后直接把生成的 openapi.json 打印出来看.

怎么跑:
    python fastapi_notes/ch06/code/01_openapi_customize.py
"""

import json
import warnings

warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402


class ItemOut(BaseModel):
    id: int = Field(description="商品 id")
    name: str = Field(description="商品名")


app = FastAPI(
    title="商品服务",
    version="1.0.0",
    description="演示 OpenAPI 文档是怎么来的",
)


@app.get(
    "/items",
    response_model=list[ItemOut],
    tags=["商品"],
    summary="商品列表",
    description="支持分页, 按 id 升序返回.",
)
def list_items(
    page: int = Query(1, ge=1, description="页码,从 1 开始"),
    size: int = Query(10, ge=1, le=50, description="每页条数"),
):
    """这个函数的 docstring 也会出现在文档里."""
    return [{"id": i, "name": f"商品{i}"} for i in range((page - 1) * size, page * size)]


@app.get("/items/{item_id}", response_model=ItemOut, tags=["商品"], summary="商品详情")
def get_item(item_id: int):
    if item_id > 100:
        raise HTTPException(status_code=404, detail="商品不存在")
    return {"id": item_id, "name": f"商品{item_id}"}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    spec = app.openapi()

    show("① 文档的顶层信息")
    print("    title      :", spec["info"]["title"])
    print("    version    :", spec["info"]["version"])
    print("    description:", spec["info"]["description"])

    show("② 接口怎么分组(tags)")
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            print(f"    {method.upper():5} {path:18} tags={op.get('tags')} summary={op.get('summary')}")

    show("③ 查询参数自动带上描述和校验")
    params = spec["paths"]["/items"]["get"]["parameters"]
    for p in params:
        print(f"    {p['name']:6} 类型={p['schema']['type']:6} 说明={p.get('description')}")
    print("    schema 里的约束:", json.dumps(params[1]["schema"], ensure_ascii=False))

    show("④ 响应模型自动变成 schema")
    schemas = spec["components"]["schemas"]
    print("    ItemOut:", json.dumps(schemas["ItemOut"], ensure_ascii=False))

    show("⑤ 但错误响应不会自动出现")
    responses = spec["paths"]["/items/{item_id}"]["get"]["responses"]
    print("    已声明的响应码:", list(responses))
    print("    → 只有 200 和 422, 404 是代码里 raise 的, 文档里看不到")
    print("    → 想让文档写出错误格式, 要显式声明 responses=(下个案例)")
