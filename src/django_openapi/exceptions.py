class RequestArgsError(Exception):
    def __init__(self, errors):
        self.errors = errors


class BadRequestError(Exception):
    """HTTP 400"""


class NotFoundError(Exception):
    """HTTP 404"""


class UnauthorizedError(Exception):
    """HTTP 401"""


class MethodNotAllowedError(Exception):
    """HTTP 405"""


class ForbiddenError(Exception):
    """HTTP 403"""


class UnsupportedMediaTypeError(Exception):
    """HTTP 415"""
