"""FastAPI 第二部分 - 案例 4-2: 把"排序"做成受控参数.

列表接口常要支持排序, 但排序字段不能直接用用户传的字符串拼进 SQL
(那就是 SQL 注入). 正确做法是白名单: 只允许有限的几个字段.

这个案例演示三种写法:
    ① 不安全: 直接把用户传的值拼进 SQL
    ② 安全: 白名单映射
    ③ 更好: 用 FastAPI 的 Literal 在入口就挡掉非法值

怎么跑:
    python fastapi_notes/ch04/code/02_sort_params.py
"""

import warnings
from typing import Literal

warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException, Query  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

import sys  # noqa: E402
from pathlib import Path  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project"))
from app.db.session import SessionLocal  # noqa: E402

app = FastAPI()

# 白名单: 用户能写的值 -> 真实的列名
SORTABLE = {
    "id": "id",
    "-id": "id DESC",
    "balance": "balance",
    "-balance": "balance DESC",
    "created_at": "created_at",
    "-created_at": "created_at DESC",
}


@app.get("/unsafe")
def unsafe(sort: str = "id"):
    """不安全的写法: 用户传什么就拼什么."""
    with SessionLocal() as db:
        try:
            rows = db.execute(text(f"SELECT id, username FROM users ORDER BY {sort} LIMIT 3")).all()
            return {"sql": f"ORDER BY {sort}", "rows": [list(r) for r in rows]}
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"SQL 出错: {type(exc).__name__}")


@app.get("/whitelist")
def whitelist(sort: str = Query("id", description="排序方式")):
    """安全写法: 不在白名单里就拒绝."""
    if sort not in SORTABLE:
        raise HTTPException(status_code=400, detail=f"sort 只支持: {list(SORTABLE)}")

    clause = SORTABLE[sort]
    with SessionLocal() as db:
        rows = db.execute(text(f"SELECT id, username FROM users ORDER BY {clause} LIMIT 3")).all()
        return {"sort": sort, "order_by": clause, "rows": [list(r) for r in rows]}


@app.get("/literal")
def literal(
    sort: Literal["id", "-id", "balance", "-balance"] = Query(
        "id", description="排序方式, 只允许这四种"
    ),
):
    """最优写法: 类型系统 + 文档一起解决, 非法值直接 422."""
    clause = SORTABLE[sort]
    with SessionLocal() as db:
        rows = db.execute(text(f"SELECT id, username FROM users ORDER BY {clause} LIMIT 3")).all()
        return {"sort": sort, "order_by": clause, "rows": [list(r) for r in rows]}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 正常排序")
        print("    /literal            ->", client.get("/literal").json()["rows"])

        show("② 不安全写法: 注入一段 SQL 试试")
        r = client.get("/unsafe", params={"sort": "id; SELECT 1"})
        print("    状态码:", r.status_code, " 响应:", r.json())

        r = client.get("/unsafe", params={"sort": "(CASE WHEN 1=1 THEN id ELSE balance END)"})
        print("    复杂表达式也被执行了:", r.status_code, r.json().get("sql"))

        show("③ 白名单写法: 非法值被挡下")
        r = client.get("/whitelist", params={"sort": "password_hash"})
        print("    状态码:", r.status_code, " 响应:", r.json()["detail"][:60], "...")

        show("④ Literal 写法: 入口就 422, 连业务逻辑都进不去")
        r = client.get("/literal", params={"sort": "password_hash"})
        print("    状态码:", r.status_code)
        print("    错误:", r.json()["detail"][0]["msg"])
        print("    → 文档里也会只列出这四种可选值")

        show("⑤ 结论")
        print("    排序/过滤字段一定要白名单, 不要把用户输入拼进 SQL")
        print("    用 Literal 还能让 /docs 自动列出可选项, 前端少踩坑")
