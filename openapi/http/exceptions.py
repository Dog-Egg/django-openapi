class HttpException(Exception):
    status = 500

    def __init__(self, body: dict = None):
        self.body = body or {}


class BadRequest(HttpException):
    status = 400
