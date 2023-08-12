from django.conf import settings
from django.http import HttpRequest

from django_openapi import exceptions
from django_openapi_schema.spectools.objects import OpenAPISpec


class BaseAuth:
    """
    认证基类。
    """

    def check_auth(self, request):
        """需实现该方法，如果认证失败，需要抛出异常。"""
        raise NotImplementedError

    def __openapispec__(self, spec, **kwargs):
        pass


class DjangoAuthBase(BaseAuth):
    def _check_auth(self, request):
        raise NotImplementedError

    def check_auth(self, request):
        if not self._check_auth(request):
            if request.user.is_authenticated:
                raise exceptions.ForbiddenError
            raise exceptions.UnauthorizedError

    def __openapispec__(self, spec: OpenAPISpec, **kwargs):
        key = "__auth__"
        spec.set_security_scheme(
            key,
            {
                "type": "apiKey",
                "name": settings.SESSION_COOKIE_NAME,
                "in": "cookie",
            },
        )
        return [{key: []}]


class IsAuthenticated(DjangoAuthBase):
    """验证用户是否登录。"""

    def _check_auth(self, request: HttpRequest):
        return request.user.is_authenticated


class IsSuperuser(DjangoAuthBase):
    """验证用户是否为超级管理员。"""

    def _check_auth(self, request: HttpRequest):
        return request.user.is_superuser  # type: ignore


class IsAdministrator(DjangoAuthBase):
    """验证用户是否为管理员。"""

    def _check_auth(self, request: HttpRequest):
        return request.user.is_staff  # type: ignore


class HasPermission(DjangoAuthBase):
    """
    验证用户是否拥有某权限。内部调用 ``request.user.has_perm`` 方法。

    :param perm: 描述权限的字符串，格式是 "<app label>.<permission codename>"。
    """

    def __init__(self, perm: str):
        self.__perm = perm

    def _check_auth(self, request: HttpRequest):
        return request.user.has_perm(self.__perm)  # type: ignore
