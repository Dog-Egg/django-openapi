"""测试 Resource & Operation 上视图装饰器"""
import functools
import typing

import pytest
from django.http import HttpRequest, HttpResponse
from django.urls import path, include

from django_openapi import OpenAPI, Resource, Operation


def view_decorator(http_methods: typing.List[str]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            if request.method not in http_methods:
                return HttpResponse(status=488)
            return func(request, *args, **kwargs)

        return wrapper

    return decorator


openapi = OpenAPI()


@Resource(
    '/',
    view_decorators=[view_decorator(['GET', 'POST', 'PUT'])],
)
class API:
    @Operation(
        view_decorators=[view_decorator(['GET'])]
    )
    def get(self):
        pass

    def post(self):
        pass

    @Operation(view_decorators=[view_decorator([])])
    def put(self):
        pass


openapi.add_resource(API)


@view_decorator(['GET', 'POST'])
def view(request, *args, **kwargs):
    return HttpResponse('ok')


urlpatterns = [
    path('a/', view),
    path('b/', include(openapi.urls))
]


@pytest.mark.urls('tests.test_view_decorator')
def test_a(client):
    assert client.get('/a/').status_code == 200
    assert client.post('/a/').status_code == 200
    assert client.put('/a/').status_code == 488


@pytest.mark.urls('tests.test_view_decorator')
def test_b(client):
    assert client.get('/b/').status_code == 200
    assert client.post('/b/').status_code == 200
    assert client.put('/b/').status_code == 488
