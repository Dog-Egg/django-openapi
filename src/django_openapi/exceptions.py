from django_openapi_schema.exceptions import ValidationError


class RequestValidationError(Exception):
    """解析请求参数/请求体是，当 Schema 对数据反序列化失败时抛出，默认为 HTTP 400 响应。"""

    def __init__(self, exc: ValidationError, location: str):
        #: 数据反序列化错误抛出的 `ValidationError <django_openapi.schema.ValidationError>` 对象。
        self.exc = exc

        #: 错误发生在请求的位置，其值为 "query", "cookie", "header" 或 "body" 中的一个。
        self.location = location


class BadRequestError(Exception):
    """处理请求数据时，在数据格式错误时抛出，默认返回 HTTP 400 响应。"""


class NotFoundError(Exception):
    """路径参数解析失败时抛出，默认返回 HTTP 404响应。"""


class UnauthorizedError(Exception):
    """权限验证错误时，当用户为验证时抛出，默认返回 HTTP 401 响应。"""


class MethodNotAllowedError(Exception):
    """请求路径时，当请求方法不存在时抛出，默认返回 HTTP 405 响应。"""


class ForbiddenError(Exception):
    """权限验证错误时，当用户权限不匹配时抛出，默认返回 HTTP 403 响应。"""


class UnsupportedMediaTypeError(Exception):
    """请求内容类型与要求不符时抛出，默认返回 HTTP 415 响应。"""
