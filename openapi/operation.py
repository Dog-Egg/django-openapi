import typing

from openapi.parameters import Parameter


class Operation:
    def __init__(
            self,
            *,
            tags: typing.List[str] = None,
            summary: str = None,
            description: str = None,
            parameters: typing.List[Parameter] = None,
            # request_body=None,
    ):
        self.tags = tags
        self.summary = summary
        self.description = description
        self.parameters = parameters or []

        for param in self.parameters:
            pass
