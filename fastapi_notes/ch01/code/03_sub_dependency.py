"""FastAPI 第二部分 - 案例 3: 依赖里还能有依赖(子依赖).

真实项目里鉴权是一层套一层的:
    解析令牌 -> 拿到用户 id -> 查出用户 -> 检查角色

每一层都可以写成独立的依赖, 后面的依赖把前面的当参数.

怎么跑:
    python fastapi_notes/ch01/code/03_sub_dependency.py
"""

import warnings

warnings.filterwarnings("ignore")

from fastapi import Depends, FastAPI, Header, HTTPException  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()

# 假数据库
USERS = {
    1: {"id": 1, "username": "张三", "roles": ["admin"]},
    2: {"id": 2, "username": "李四", "roles": ["viewer"]},
}
TOKENS = {"token-1": 1, "token-2": 2}


# ------------------------------------------------ 第 1 层: 解析令牌
def get_user_id(authorization: str = Header(default="")) -> int:
    """从请求头里解析出用户 id."""
    token = authorization.replace("Bearer ", "")
    if token not in TOKENS:
        raise HTTPException(status_code=401, detail="令牌无效")
    return TOKENS[token]


# ------------------------------------------------ 第 2 层: 查用户
def get_current_user(user_id: int = Depends(get_user_id)) -> dict:
    """依赖里用 Depends(get_user_id) - 这就是子依赖."""
    user = USERS.get(user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


# ------------------------------------------------ 第 3 层: 查角色
def require_admin(user: dict = Depends(get_current_user)) -> dict:
    """在第 2 层的基础上再判断角色."""
    if "admin" not in user["roles"]:
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return user


@app.get("/profile")
def profile(user: dict = Depends(get_current_user)):
    """只要登录就能访问."""
    return {"用户名": user["username"], "角色": user["roles"]}


@app.get("/admin/users")
def admin_users(user: dict = Depends(require_admin)):
    """要管理员才能访问 - 依赖链有三层."""
    return {"操作人": user["username"], "用户列表": list(USERS.values())}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 没带令牌 -> 第 1 层就拦下(401)")
        print("    GET /profile           ->", client.get("/profile").status_code, client.get("/profile").json())

        show("② 带普通用户令牌 -> 第 2 层通过")
        r = client.get("/profile", headers={"Authorization": "Bearer token-2"})
        print("    GET /profile           ->", r.status_code, r.json())

        show("③ 普通用户访问管理员接口 -> 第 3 层拦下(403)")
        r = client.get("/admin/users", headers={"Authorization": "Bearer token-2"})
        print("    GET /admin/users       ->", r.status_code, r.json())

        show("④ 管理员令牌 -> 三层全过")
        r = client.get("/admin/users", headers={"Authorization": "Bearer token-1"})
        print("    GET /admin/users       ->", r.status_code, r.json())

        show("⑤ 依赖链的执行顺序")
        print("    get_user_id  ->  get_current_user  ->  require_admin  ->  路由函数")
        print("    任何一层抛异常, 后面的都不执行")

        show("⑥ 依赖缓存也在这里生效")
        print("    同一次请求里 get_user_id 只执行一次,")
        print("    即使 get_current_user 和 require_admin 都间接依赖它")
