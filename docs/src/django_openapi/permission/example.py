from django_openapi import Operation, Resource, permissions


@Resource("/to/path")
class API:
    @Operation(
        permission=permissions.IsAdministrator,
    )
    def get(self):
        ...
