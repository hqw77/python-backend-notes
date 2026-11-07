"""分页参数依赖.

原来每个列表接口都要写这三个参数:

    def list_users(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
    ): ...

现在打包成一个类, 路由里只写 `p: PageParams = Depends()`.

FastAPI 会把 __init__ 的参数当成查询参数解析, 校验规则(ge/le)也一起生效.
"""

from fastapi import Query


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码,从 1 开始"),
        size: int = Query(10, ge=1, le=100, description="每页条数,最大 100"),
    ) -> None:
        self.page = page
        self.size = size
        self.offset = (page - 1) * size

    def __repr__(self) -> str:
        return f"<PageParams page={self.page} size={self.size} offset={self.offset}>"
