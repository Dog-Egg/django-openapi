from django_openapi import Resource, Operation
from django_openapi.permissions import IsAdministrator


@Resource('/path')
class API:
    @Operation(
        # GET请求需要管理员权限
        # highlight-next-line
        permission=IsAdministrator
    )
    def get(self):
        return 'ok'


@Resource(
    '/path2',
    # 该路由下的所有请求方法都需要管理员权限
    # highlight-next-line
    permission=IsAdministrator
)
class API2:
    def get(self):
        return 'ok'
