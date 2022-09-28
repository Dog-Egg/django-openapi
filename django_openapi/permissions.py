import typing

from django.http import HttpRequest

from django_openapi.spec import utils as _spec
from django_openapi.exceptions import Forbidden, Unauthorized
from django_openapi.utils.functional import make_instance


class _OperationMixin:
    def __and__(self, other):
        return _AndOperation(self, other)

    def __or__(self, other):
        return _OrOperation(self, other)


class _OperationMixinMeta(_OperationMixin, type):
    pass


class BasePermission(_OperationMixin, metaclass=_OperationMixinMeta):
    security: typing.Optional[list] = None

    def check_permission(self, request):
        raise NotImplementedError

    def to_spec(self, spec_id):
        if self.security is not None:
            return self.security
        return _spec.Collection(spec_id).security or [{'_$unknown$_': []}]


class _AndOperation(BasePermission):
    def __init__(self, p1, p2):
        self.p1 = make_instance(p1)
        self.p2 = make_instance(p2)

    def check_permission(self, request):
        self.p1.check_permission(request)
        self.p2.check_permission(request)


class _OrOperation(BasePermission):
    def __init__(self, p1, p2):
        self.p1 = make_instance(p1)
        self.p2 = make_instance(p2)

    def check_permission(self, request):
        errors = []
        for p in (self.p1, self.p2):
            try:
                p.check_permission(request)
            except Exception as e:
                errors.append(e)
            else:
                return
        raise errors[-1]


class BaseDjangoUserAuth(BasePermission):
    def has_permission(self, request: HttpRequest):
        raise NotImplementedError

    def check_permission(self, request):
        if not self.has_permission(request):
            if request.user and request.user.is_authenticated:
                raise Forbidden
            raise Unauthorized


class IsAuthenticated(BaseDjangoUserAuth):
    def has_permission(self, request: HttpRequest):
        return request.user and request.user.is_authenticated


class IsSuperuser(BaseDjangoUserAuth):
    def has_permission(self, request: HttpRequest):
        return request.user and request.user.is_superuser


class IsAdministrator(BaseDjangoUserAuth):
    def has_permission(self, request: HttpRequest):
        return request.user and request.user.is_staff


class HasPermission(BaseDjangoUserAuth):
    def __init__(self, perm):
        self.perm = perm

    def has_permission(self, request: HttpRequest):
        return request.user and request.user.has_perm(self.perm)
