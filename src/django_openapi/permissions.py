from django.conf import settings
from django.http import HttpRequest

from django_openapi_schema.spectools.objects import OpenAPISpec, Protect
from django_openapi_schema.utils import make_instance


class _OperationMixin:
    def __and__(self, other):
        return _AndOperation(self, other)

    def __or__(self, other):
        return _OrOperation(self, other)


class _OperationMixinMeta(_OperationMixin, type):
    pass


class BasePermission(_OperationMixin, metaclass=_OperationMixinMeta):
    """
    权限基类。
    """

    def has_permission(self, request) -> bool:
        raise NotImplementedError

    def __openapispec__(self, spec: OpenAPISpec):
        key = "__auth__"
        spec.add_security(
            {
                key: {
                    "type": "apiKey",
                    "name": settings.SESSION_COOKIE_NAME,
                    "in": "cookie",
                },
            }
        )
        return [{key: Protect([])}]


class _AndOperation(BasePermission):
    def __init__(self, p1, p2):
        self.__p1 = make_instance(p1)
        self.__p2 = make_instance(p2)

    def has_permission(self, request):
        return self.__p1.has_permission(request) and self.__p2.has_permission(request)


class _OrOperation(BasePermission):
    def __init__(self, p1, p2):
        self.__p1 = make_instance(p1)
        self.__p2 = make_instance(p2)

    def has_permission(self, request):
        return self.__p1.has_permission(request) or self.__p2.has_permission(request)


class IsAuthenticated(BasePermission):
    """验证用户是否登录。"""

    def has_permission(self, request: HttpRequest):
        return request.user.is_authenticated


class IsSuperuser(BasePermission):
    """验证用户是否为超级管理员。"""

    def has_permission(self, request: HttpRequest):
        return request.user.is_superuser  # type: ignore


class IsAdministrator(BasePermission):
    """验证用户是否为管理员。"""

    def has_permission(self, request: HttpRequest):
        return request.user.is_staff  # type: ignore


class HasPermission(BasePermission):
    """
    验证用户是否拥有某权限。内部调用 ``request.user.has_perm`` 方法。

    :param perm: 描述权限的字符串，格式是 "<app label>.<permission codename>"。
    """

    def __init__(self, perm: str):
        self.__perm = perm

    def has_permission(self, request: HttpRequest):
        return request.user.has_perm(self.__perm)  # type: ignore
