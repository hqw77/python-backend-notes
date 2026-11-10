"""FastAPI 第二部分 - 案例 3: BackgroundTasks.

场景: 注册成功后要发一封欢迎邮件.
    同步发 -> 用户要等邮件服务器响应(可能 0.5~2 秒)
    后台发 -> 接口立刻返回, 邮件在响应之后慢慢发

BackgroundTasks 就干这个: 把"不需要用户等待"的活挪到响应之后.

怎么跑:
    python fastapi_notes/ch03/code/03_background_tasks.py
"""

import time
import warnings

warnings.filterwarnings("ignore")

from fastapi import BackgroundTasks, FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

app = FastAPI()

sent: list[str] = []


def send_welcome_email(email: str) -> None:
    """模拟发邮件, 耗时 0.3 秒."""
    time.sleep(0.3)
    sent.append(email)


def always_fail(job_id: str) -> None:
    """模拟一个必定失败的后台任务."""
    raise RuntimeError(f"任务 {job_id} 失败了")


# ---------------------------------------------------------------- 同步版
@app.post("/register-sync")
def register_sync():
    t0 = time.perf_counter()
    send_welcome_email("a@example.com")
    cost = time.perf_counter() - t0
    return {"handler_cost": round(cost, 3), "说明": "请求要等邮件发完"}


# ---------------------------------------------------------------- 后台版
@app.post("/register-background")
def register_background(background: BackgroundTasks):
    t0 = time.perf_counter()
    background.add_task(send_welcome_email, "b@example.com")
    cost = time.perf_counter() - t0
    return {"handler_cost": round(cost, 3), "说明": "请求不等邮件"}


# ---------------------------------------------------------------- 失败版
@app.post("/register-fail")
def register_fail(background: BackgroundTasks):
    background.add_task(always_fail, "job-1")
    return {"msg": "接口正常返回"}


def show(title: str) -> None:
    print(f"\n--- {title} ---")


if __name__ == "__main__":
    with TestClient(app) as client:
        show("① 同步发邮件: 路由要等邮件发完")
        r = client.post("/register-sync")
        print("    路由内耗时:", r.json()["handler_cost"], "秒")
        print("    说明:", r.json()["说明"])

        show("② 后台发邮件: 路由立刻返回")
        sent.clear()
        r = client.post("/register-background")
        print("    路由内耗时:", r.json()["handler_cost"], "秒")
        print("    说明:", r.json()["说明"])
        print("    邮件发了吗:", sent, "(响应之后才发)")

        show("③ 后台任务和响应是分开的")
        print("    路由函数只负责 add_task, 立刻 return")
        print("    FastAPI 把响应发出去之后, 才执行 send_welcome_email")
        print("    → 用户感知的延迟从 0.3 秒降到 ~0.001 秒")

        show("④ 后台任务失败了会怎样")
        sent.clear()
        # TestClient 默认会把服务端异常抛给调用方, 关掉它才看得到"真实服务器"的行为
        real_client = TestClient(app, raise_server_exceptions=False)
        r = real_client.post("/register-fail")
        print("    响应状态码:", r.status_code, " 响应体:", r.json())
        print("    接口没有报错, 用户看到的是成功")
        print("    → 异常只出现在服务端日志里, 客户端完全不知道")
        print("    → 后台任务的异常不会影响响应, 也不会自动重试")
        print("    → 生产环境要在任务函数里自己 try/except + 打日志")

        show("⑤ BackgroundTasks 的局限")
        print("    任务是'进程内'的: 进程重启/崩溃, 没跑完的任务直接丢")
        print("    没有重试, 没有失败队列, 没有可视化的任务状态")
        print("    只适合'丢了也不致命'的事: 发通知, 写日志, 清临时文件")

        show("⑥ 什么时候该换成 Celery / RQ")
        print("    任务要重试           -> 需要队列")
        print("    任务要跑几分钟以上   -> 需要独立 worker")
        print("    任务要能看到状态     -> 需要结果存储")
        print("    任务量很大要扩机器   -> 需要分布式")
