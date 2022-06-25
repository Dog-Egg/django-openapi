import typing


class ValidationError(Exception):
    def __init__(self, message: typing.Any):
        self.message = message
