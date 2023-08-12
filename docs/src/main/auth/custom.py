from django_openapi import Operation, Resource
from django_openapi.auth import BaseAuth
from django_openapi.exceptions import UnauthorizedError


def get_user(request):
    # 获取用户函数
    ...


class MyAuthBase(BaseAuth):
    def __openapispec__(self, spec, **kwargs):
        # 该方法用于生成 OAS security 的定义，
        # 如果不需要向 OAS 提示认证定义，可忽略实现该方法。

        # spec.set_security_scheme 函数向 OAS securitySchemes
        # 部分设置一个 Security Scheme Objects.
        spec.set_security_scheme(
            "token",
            {
                "type": "http",
                "scheme": "Bearer",
            },
        )

        # 返回值用于为 Operation 设置 security
        return [{"token": []}]


class IsAuthenticated(MyAuthBase):
    """验证用户是否登录"""

    def check_auth(self, request):
        user = get_user(request)
        if not user:
            raise UnauthorizedError


@Resource("/to/path")
class API:
    @Operation(auth=IsAuthenticated)
    def get(self):
        ...
