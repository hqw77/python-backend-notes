"""统一的错误响应格式.

全项目的业务异常最终都长这样:

    {"detail": "用户 99999 不存在"}

把它定义成模型, 是为了在 OpenAPI 文档里声明错误响应,
让前端能按 schema 生成类型, 不用猜.

注意: 这里只描述格式, 真正的返回由 main.py 的 exception_handler 拼出来.
两边必须保持一致, 否则文档就是在撒谎.
"""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    detail: str = Field(description="错误说明")


# 常用的错误响应声明, 直接写进路由的 responses 参数
RESP_400 = {400: {"model": ErrorResponse, "description": "参数不合法"}}
RESP_401 = {401: {"model": ErrorResponse, "description": "未认证"}}
RESP_403 = {403: {"model": ErrorResponse, "description": "没有权限"}}
RESP_404 = {404: {"model": ErrorResponse, "description": "资源不存在"}}
RESP_409 = {409: {"model": ErrorResponse, "description": "资源冲突"}}
