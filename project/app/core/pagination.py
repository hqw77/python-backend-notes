"""分页与排序参数依赖.

原来每个列表接口都要写这三个参数:

    def list_users(
        page: int = Query(1, ge=1),
        size: int = Query(10, ge=1, le=100),
        db: Session = Depends(get_db),
    ): ...

现在打包成一个类, 路由里只写 `p: PageParams = Depends()`.

FastAPI 会把 __init__ 的参数当成查询参数解析, 校验规则(ge/le/Literal)也一起生效.

排序字段用 Literal 而不是自由的字符串:
    - 非法值在入口就被挡成 422, 进不到业务逻辑
    - /docs 里会自动列出可选值
    - 从根上避免"用户输入拼进 SQL"的注入风险
"""

from typing import Literal

from fastapi import Query

# 允许的排序方式: 不带减号是升序, 带减号是降序
SortField = Literal["id", "-id", "balance", "-balance", "created_at", "-created_at"]


class PageParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码,从 1 开始"),
        size: int = Query(10, ge=1, le=100, description="每页条数,最大 100"),
        sort: SortField = Query("-id", description="排序方式, 减号表示降序"),
    ) -> None:
        self.page = page
        self.size = size
        self.sort = sort
        self.offset = (page - 1) * size

    def __repr__(self) -> str:
        return (
            f"<PageParams page={self.page} size={self.size} "
            f"sort={self.sort} offset={self.offset}>"
        )
