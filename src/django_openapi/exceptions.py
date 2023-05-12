import typing
from django.http.response import HttpResponseBase, HttpResponse


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
