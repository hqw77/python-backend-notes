"""FastAPI 第二部分 - 案例 7-2: 用事务回滚做测试隔离.

问题: 测试会改数据. 跑完要还原, 否则第二次跑就失败.
三种做法:
    ① 每个测试自己清理(现在项目用的方式)
    ② 用例结束后 rollback 事务(最快)
    ③ 用独立的测试库(最干净)

这个案例演示 ②: 改完不提交, 直接回滚, 数据库一点没变.

怎么跑:
    python fastapi_notes/ch07/code/02_transaction_rollback.py
"""

import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "project"))
warnings.filterwarnings("ignore")

from sqlalchemy import select  # noqa: E402

from app.db.session import SessionLocal  # noqa: E402
from app.models import User  # noqa: E402


def show(title: str) -> None:
    print(f"\n--- {title} ---")


def read_balance(user_id: int) -> str:
    """用一个全新的 Session 读余额, 代表"数据库里真实的值"."""
    with SessionLocal() as db:
        user = db.get(User, user_id)
        return str(user.balance)


if __name__ == "__main__":
    user_id = 1
    original = read_balance(user_id)

    show("① 数据库里的原始值")
    print("    balance =", original)

    show("② 在事务里改, 但不提交")
    db = SessionLocal()
    try:
        user = db.get(User, user_id)
        user.balance = user.balance - 100
        db.flush()                          # 写进事务(还没 commit)

        print("    事务内读到:  ", db.get(User, user_id).balance)
        print("    另一个 Session: ", read_balance(user_id), "(看不到改动)")
        print("    → 未提交的改动只有当前事务能看到")

        show("③ 回滚: 改动全部丢弃")
        db.rollback()
        print("    回滚后本事务读:", db.get(User, user_id).balance)
        print("    另一个 Session: ", read_balance(user_id))
    finally:
        db.close()

    show("④ 结论")
    print("    恢复成:      ", read_balance(user_id))
    print("    原始值也是:  ", original)
    print("    → 测试里用这个模式, 跑多少遍都不会污染数据")

    show("⑤ 三种隔离方式的取舍")
    print("    自己清理   : 简单, 但漏一处就留垃圾(需要 try/finally)")
    print("    事务回滚   : 最快, 但要求被测代码和测试共用同一个 Session")
    print("    独立测试库 : 最干净, 但要建库建表, 初始化慢")
