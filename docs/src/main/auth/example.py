from django_openapi import Operation, Resource
from django_openapi.auth import IsAdministrator


@Resource("/to/path")
class API:
    @Operation(
        auth=IsAdministrator,
    )
    def get(self):
        ...
