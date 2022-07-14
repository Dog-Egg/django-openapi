class HttpException(Exception):
    status = 500

    def __init__(self, body: dict = None):
        self.body = body or {}


class BadRequest(HttpException):
    status = 400


class Unauthorized(HttpException):
    status = 401


class Forbidden(HttpException):
    status = 403


class NotFound(HttpException):
    status = 404


class MethodNotAllowed(HttpException):
    status = 405
