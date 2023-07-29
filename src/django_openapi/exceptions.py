import typing
from http import HTTPStatus

from django_openapi_schema.exceptions import ValidationError


class RequestValidationError(Exception):
    """解析请求参数/请求体是，当 Schema 对数据反序列化失败时抛出，默认为 HTTP 400 响应。"""

    def __init__(self, exc: ValidationError, location: str):
        #: 数据反序列化错误抛出的 `ValidationError <django_openapi.schema.ValidationError>` 对象。
        self.exc = exc

        #: 错误发生在请求的位置，其值为 "query", "cookie", "header" 或 "body" 中的一个。
        self.location = location


class HTTPError(Exception):
    status_code = 500

    def __init__(self, reason: typing.Optional[str] = None) -> None:
        if reason is None:
            reason = HTTPStatus(self.status_code).phrase
        self.reason: str = reason


class BadRequestError(HTTPError):
    """处理请求数据时，在数据格式错误时抛出，默认返回 HTTP 400 响应。"""

    status_code = 400


class NotFoundError(HTTPError):
    """路径参数解析失败时抛出，默认返回 HTTP 404响应。"""

    status_code = 404


class UnauthorizedError(HTTPError):
    """认证失败时抛出，默认返回 HTTP 401 响应。"""

    status_code = 401


class MethodNotAllowedError(HTTPError):
    """请求路径时，当请求方法不存在时抛出，默认返回 HTTP 405 响应。"""

    status_code = 405


class ForbiddenError(HTTPError):
    """授权失败时抛出，默认返回 HTTP 403 响应。"""

    status_code = 403


class UnsupportedMediaTypeError(HTTPError):
    """请求内容类型与要求不符时抛出，默认返回 HTTP 415 响应。"""

    status_code = 415
