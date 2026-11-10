"""FastAPI 第二部分 - 案例 7-1: dependency_overrides.

测试时经常想把"真依赖"换成"假的":
    真数据库 -> 内存字典
    真登录   -> 直接注入一个假用户

app.dependency_overrides 就是干这个的: 一张"依赖 -> 替代实现"的表.

怎么跑:
    python fastapi_notes/ch07/code/01_dependency_overrides.py
"""

import warnings

warnings.filterwarnings("ignore")

from fastapi import Depends, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()


def get_db():
    """真依赖: 假装连了数据库."""
    return {"db": "real-mysql"}


def get_user():
    """真依赖: 假装查了用户."""
    return {"user": "real-user"}


@app.get("/info")
def info(db=Depends(get_db), user=Depends(get_user)):
    return {"db": db, "user": user}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 没有覆盖: 用的是真依赖")
        print("    ", client.get("/info").json())

        show("② 只覆盖 get_db, get_user 保持原样")
        app.dependency_overrides[get_db] = lambda: {"db": "fake-dict"}
        print("    ", client.get("/info").json())
        print("    → 只有被覆盖的那个变了, 其他不受影响")

        show("③ 再覆盖 get_user")
        app.dependency_overrides[get_user] = lambda: {"user": "fake-user"}
        print("    ", client.get("/info").json())

        show("④ 清空覆盖, 恢复原状")
        app.dependency_overrides.clear()
        print("    ", client.get("/info").json())
        print("    → 一定要在测试结束后 clear(), 否则会影响其他测试")

        show("⑤ 为什么要用它")
        print("    跳过登录: 不用真的注册+登录+拿令牌")
        print("    跳过数据库: 不依赖 MySQL 是否启动")
        print("    模拟异常分支: 让依赖直接抛异常, 测错误处理")
        print("    → 测试更快, 更稳, 更好写")

        show("⑥ 在 pytest 里的标准写法")
        print("    @pytest.fixture")
        print("    def fake_user(client):")
        print("        app.dependency_overrides[get_current_user] = lambda: FakeUser()")
        print("        yield")
        print("        app.dependency_overrides.clear()   # fixture 负责清理")
