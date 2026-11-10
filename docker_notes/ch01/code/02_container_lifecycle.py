"""Docker 第一章 - 案例 2: 容器的生命周期.

镜像和容器的关系: 镜像是"安装包", 容器是"跑起来的进程".
一条命令就能看出区别:

    docker images     有东西
    docker ps         没东西(没跑)
    docker run ...    跑起来
    docker ps         有了
    docker stop/rm    又没了, 但镜像还在

这个案例用一个很小的 alpine 镜像演示, 不碰项目的数据.

怎么跑:
    python docker_notes/ch01/code/02_container_lifecycle.py
"""

import subprocess
import sys


def run(*args: str) -> tuple[int, str]:
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


NAME = "pbn-demo"


def cleanup() -> None:
    run("docker", "rm", "-f", NAME)


if __name__ == "__main__":
    if not docker_ok():
        print("    这个案例需要在能访问 docker 的终端里跑")
        sys.exit(0)

    show("① 先确认演示容器不存在")
    cleanup()
    code, out = run("docker", "ps", "-a", "--filter", f"name={NAME}", "--format", "{{.Names}}")
    print("    同名容器:", out or "(没有)")

    show("② 跑一个容器: 执行 echo 后退出")
    code, out = run("docker", "run", "--name", NAME, "alpine:3", "echo", "hello from container")
    print("    退出码:", code)
    print("    容器输出:", out)
    print("    → 这个容器跑完就退出了, 但还留着(状态是 Exited)")

    show("③ 看它还在不在")
    code, out = run("docker", "ps", "-a", "--filter", f"name={NAME}", "--format", "{{.Names}}  {{.Status}}")
    print("    " + (out or "(没有)"))

    show("④ 删掉容器, 镜像还在")
    cleanup()
    code, out = run("docker", "ps", "-a", "--filter", f"name={NAME}", "--format", "{{.Names}}")
    print("    容器:", out or "(已删除)")
    code, out = run("docker", "images", "alpine", "--format", "{{.Repository}}:{{.Tag}}  {{.Size}}")
    print("    镜像:", out or "(没有)")

    show("⑤ 三个概念的关系")
    print("    Dockerfile -> 构建出 镜像(image)")
    print("    镜像       -> 跑起来是 容器(container)")
    print("    容器       -> 删掉不影响镜像, 下次还能再跑")
    print("    → 所以'重建环境'才那么快: 镜像在本地, 不用重新下载")
