"""用户详情的缓存(Cache-Aside).

读: 先查缓存 -> 未命中查库 -> 回写缓存
写: 由 user_service 在改完数据库后删除缓存, 这里只负责读

关键设计: 缓存里存的是 UserOut(纯数据), 不是 ORM 的 User 对象.
    ORM 对象和 Session 绑定, 存进缓存再取出来会变成 detached 实例,
    一访问属性就报 DetachedInstanceError.
    UserOut 是 Pydantic 模型, model_dump() 之后就是普通字典, 可以安全序列化.
"""

from sqlalchemy.orm import Session

from app.schemas.user import UserOut
from app.services import cache, user_service


def get_user_out(db: Session, user_id: int) -> UserOut:
    """按 id 取用户详情, 带缓存."""
    key = cache.user_key(user_id)

    cached = cache.get_json(key)
    if cached is not None:
        return UserOut.model_validate(cached)          # 命中

    user = user_service.get_user(db, user_id)          # 未命中, 查库; 查不到抛 404
    out = UserOut.model_validate(user)

    # mode="json" 会把 Decimal / datetime 转成可序列化的字符串
    cache.set_json(key, out.model_dump(mode="json"))
    return out
