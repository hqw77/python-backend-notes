"""通知服务: 发送欢迎通知 / 后续可以扩展成邮件, 短信, 站内信.

注意这里只打日志, 不真的发邮件.
真实项目里这里会调 SMTP 或第三方邮件 API, 那一步往往要几百毫秒,
所以放在后台任务里执行, 不阻塞注册接口的响应.
"""

import logging

logger = logging.getLogger("app.notify")


def send_welcome_notice(username: str) -> None:
    """发送欢迎通知.

    后台任务的异常不会影响已经返回的响应, 所以这里必须自己兜住,
    否则错误会被静默吞掉, 排查时很难发现.
    """
    try:
        logger.info("发送欢迎通知给 %s", username)
    except Exception:                       # pragma: no cover - 兜底分支
        logger.exception("发送欢迎通知失败: %s", username)
