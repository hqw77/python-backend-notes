"""Docker 第一章 - 案例 1: 先看清环境.

跑任何 docker 命令之前, 先确认三件事:
    Docker 是否安装(docker --version)
    daemon 是否在跑(docker info / version 的 Server 部分)
    本地有哪些镜像(docker images)

怎么跑:
    python docker_notes/ch01/code/01_check_env.py

注意: 这个脚本通过 subprocess 调 docker CLI, 所以你本机要装 Docker Desktop.
"""

import subprocess
import sys


def run(*args: str) -> tuple[int, str]:
    """执行一条命令, 返回 (退出码, 输出)."""
    result = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return result.returncode, (result.stdout or result.stderr).strip()


def show(title: str) -> None:
    print(f"\n--- {title} ---")


def docker_ok() -> bool:
    """先探一下 docker 能不能用, 不能用就给一句人话提示."""
    result = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if result.returncode == 0 and result.stdout.strip():
        return True
    print("    !! 连不上 Docker daemon")
    print("       常见原因: Docker Desktop 没启动, 或当前终端没有权限访问 docker 的命名管道")
    print("       处理: 打开 Docker Desktop 等它变绿; 仍失败就换一个普通终端重跑")
    return False


if __name__ == "__main__":
    show("① docker CLI 版本")
    code, out = run("docker", "--version")
    print("    退出码:", code)
    print("    输出  :", out)

    show("② daemon 是否在跑(这一条最容易失败)")
    code, out = run("docker", "version", "--format", "{{.Server.Version}}")
    if code == 0 and out:
        print("    Server 版本:", out)
        print("    → daemon 正常, 可以继续")
    else:
        print("    拿不到 Server 版本")
        print("    → Docker Desktop 没启动, 或当前终端拿不到 docker 的命名管道权限")
        print("    → 处理: 打开 Docker Desktop 等它变绿, 然后换一个普通终端重跑本脚本")
        sys.exit(0)

    show("③ 本地镜像")
    code, out = run("docker", "images", "--format", "{{.Repository}}:{{.Tag}}  {{.Size}}")
    for line in out.splitlines()[:10]:
        print("    " + line)

    show("④ 正在运行的容器")
    code, out = run("docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}")
    if out:
        for line in out.splitlines():
            print("    " + line)
    else:
        print("    (没有运行中的容器)")
