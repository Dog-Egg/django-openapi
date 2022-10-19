"""权限"""
import inspect
from unittest import mock

import pytest

from django_openapi import Operation, permissions
from django_openapi.permissions import BasePermission
from django_openapi.urls import reverse
from tests.utils import TestResource, ResourceView, itemgetter


@TestResource(permission=permissions.IsAuthenticated)
class ResourceA(ResourceView):
    @Operation(summary='仅需登录')
    def get(self):
        pass

    @Operation(
        summary='需要管理员权限',
        permission=permissions.IsAdministrator,
    )
    def post(self):
        pass

    @Operation(
        summary='需要超级管理员权限',
        permission=permissions.IsSuperuser(),
    )
    def delete(self):
        pass


def test_request(client, django_user_model, oas):
    admin = django_user_model.objects.create_user(username='user', is_staff=True)

    assert client.get(reverse(ResourceA)).status_code == 401
    assert client.post(reverse(ResourceA)).status_code == 401

    client.force_login(admin)
    assert client.post(reverse(ResourceA)).status_code == 200

    assert client.delete(reverse(ResourceA)).status_code == 403

    assert itemgetter(oas, ['paths', reverse(ResourceA), 'get', 'security']) == [{'_$unknown$_': []}]


def test_and_operation():
    class Permission1(BasePermission):
        def check_permission(self, request):
            m(1)

    class Permission2(BasePermission):
        def check_permission(self, request):
            m(2)

    m = mock.Mock()
    (Permission1() & Permission2()).check_permission('r')
    assert m.call_args_list == [mock.call(1), mock.call(2)]

    m = mock.Mock()
    (Permission2() & Permission1()).check_permission('r')
    assert m.call_args_list == [mock.call(2), mock.call(1)]


def test_or_operation():
    class Permission1(BasePermission):
        def check_permission(self, request):
            m(1)

    class Permission2(BasePermission):
        def check_permission(self, request):
            m(2)

    m = mock.Mock()
    (Permission1() | Permission2()).check_permission('r')
    assert m.call_args_list == [mock.call(1)]

    m = mock.Mock()
    (Permission2() | Permission1()).check_permission('r')
    assert m.call_args_list == [mock.call(2)]


def test_or_operation2():
    class Permission1(BasePermission):
        def check_permission(self, request):
            m(1)
            raise ValueError

    class Permission2(BasePermission):
        def check_permission(self, request):
            m(2)

    class Permission3(BasePermission):
        def check_permission(self, request):
            raise KeyError

    m = mock.Mock()
    (Permission1() | Permission2()).check_permission('r')
    assert m.call_args_list == [mock.call(1), mock.call(2)]

    # 或运算失败抛出最后一个权限的异常
    with pytest.raises(KeyError):
        (Permission1() | Permission3()).check_permission('r')


@pytest.mark.parametrize(
    'p1,p2',
    [
        (permissions.IsSuperuser, permissions.IsAdministrator),
        (permissions.IsSuperuser(), permissions.IsAdministrator),
        (permissions.IsSuperuser, permissions.IsAdministrator()),
        (permissions.IsSuperuser(), permissions.IsAdministrator()),

        (permissions.IsAdministrator, permissions.IsSuperuser),
        (permissions.IsAdministrator(), permissions.IsSuperuser),
        (permissions.IsAdministrator, permissions.IsSuperuser()),
        (permissions.IsAdministrator(), permissions.IsSuperuser()),
    ]
)
def test_mixin_operation(p1, p2):
    def return_cls(o):
        return o if inspect.isclass(o) else type(o)

    p1_cls = return_cls(p1)
    p2_cls = return_cls(p2)

    p = p1 | p2
    assert isinstance(p, permissions._OrOperation)
    assert isinstance(p.p1, p1_cls)
    assert isinstance(p.p2, p2_cls)

    p = p1 & p2
    assert isinstance(p, permissions._AndOperation)
    assert isinstance(p.p1, p1_cls)
    assert isinstance(p.p2, p2_cls)


def test_priority():
    """测试运算优先级"""
    # 先 and 后 or
    p = permissions.IsSuperuser | permissions.IsAdministrator & permissions.IsAuthenticated
    assert isinstance(p, permissions._OrOperation)
    assert isinstance(p.p1, permissions.IsSuperuser)
    assert isinstance(p.p2, permissions._AndOperation)
    assert isinstance(p.p2.p1, permissions.IsAdministrator)
    assert isinstance(p.p2.p2, permissions.IsAuthenticated)

    p = (permissions.IsSuperuser | permissions.IsAdministrator) & permissions.IsAuthenticated
    assert isinstance(p, permissions._AndOperation)
    assert isinstance(p.p1, permissions._OrOperation)
    assert isinstance(p.p1.p1, permissions.IsSuperuser)
    assert isinstance(p.p1.p2, permissions.IsAdministrator)
    assert isinstance(p.p2, permissions.IsAuthenticated)
