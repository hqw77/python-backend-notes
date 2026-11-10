"""FastAPI 第二部分 - 案例 4-1: ORM 对象和 DTO 的区别.

为什么 service 层不该把 ORM 对象直接往上抛:
    ORM 对象和 Session 绑在一起, Session 一关, 用到"还没加载的属性"
    (比如关系属性 roles) 就会报 DetachedInstanceError.

DTO(Pydantic 模型) 是纯数据, 随便传, 随便序列化, 过期也不会炸.

怎么跑:
    python fastapi_notes/ch04/code/01_orm_vs_dto.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project"))
warnings.filterwarnings("ignore")

from app.db.session import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402
from app.schemas.user import UserOut  # noqa: E402


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    show("① ORM 对象: 已加载的字段, Session 关了也能读")
    with SessionLocal() as db:
        user = db.get(User, 1)
        print("    Session 里:      ", user.username, user.balance)

    print("    Session 关掉后:  ", user.username, user.balance, "(还能读, 因为已经加载了)")

    show("② ORM 对象: 未加载的关系属性, Session 关了就读不了")
    with SessionLocal() as db:
        user = db.get(User, 1)
        print("    Session 里: 只取了用户对象, 故意不碰 roles")

    try:
        print("    Session 关掉后再访问 roles:", [r.name for r in user.roles])
    except Exception as exc:
        print("    报错了:", type(exc).__name__)
        print("    → 这就是 DetachedInstanceError: 对象离开了 Session, 没法再查库")
        print("    → 如果 Session 里访问过一次, 数据已在内存, 关掉后还能读(所以容易漏测)")

    show("③ DTO: 在 Session 里就转好, 出去随便用")
    with SessionLocal() as db:
        user = db.get(User, 1)
        dto = UserOut.model_validate(user)          # 在 Session 内转换
        print("    转成 DTO:", dto.username, dto.balance)

    print("    Session 关掉后读 DTO:", dto.username, dto.balance)
    print("    DTO 转成 dict:      ", dto.model_dump(mode="json"))

    show("④ DTO 还能直接 JSON 序列化, ORM 对象不行")
    import json

    try:
        json.dumps(user.__dict__, default=str)
        print("    ORM 对象: 得用 default=str 兜底, 而且会带出 _sa_instance_state")
    except Exception as exc:
        print("    ORM 对象序列化失败:", type(exc).__name__)

    print("    DTO 序列化:", json.dumps(dto.model_dump(mode="json"), ensure_ascii=False)[:80], "...")

    show("⑤ 结论")
    print("    service 层内部可以用 ORM 对象, 但跨层返回时转成 DTO")
    print("    好处: 不泄漏模型细节, 能安全缓存(见 redis ch03), 能自由序列化")
