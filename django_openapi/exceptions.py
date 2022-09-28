import typing
from django.http.response import HttpResponseBase, HttpResponse


class RaiseResponse(Exception):
    def __init__(self, response: HttpResponseBase):
        self.response = response


def abort(status_or_response: typing.Union[int, HttpResponseBase]):
    if isinstance(status_or_response, HttpResponseBase):
        response = status_or_response
    else:
        response = HttpResponse(status=status_or_response)
    raise RaiseResponse(response)


class RequestArgsError(Exception):
    def __init__(self, errors):
        self.errors = errors


class BadRequest(Exception):
    pass


class NotFound(Exception):
    pass


class Unauthorized(Exception):
    pass


class MethodNotAllowed(Exception):
    pass


class Forbidden(Exception):
    pass


class UnsupportedMediaType(Exception):
    pass

