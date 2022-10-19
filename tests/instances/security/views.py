from django_openapi import Resource, Operation, permissions


@Resource('/')
class Res:
    def __init__(self, request):
        pass

    def get(self):
        pass

    @Operation(permission=permissions.IsAdministrator)
    def post(self):
        pass

    class Permission(permissions.BasePermission):
        security: list = []  # 删除顶级声明

    @Operation(permission=Permission)
    def put(self):
        pass
