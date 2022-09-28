from django_openapi import Operation
from django_openapi.exceptions import NotFound
from django_openapi.parameters import Query
from django_openapi.schema import schemas
from .exceptions import MyError
from tests.utils import TestResource, ResourceView


@TestResource
class Res(ResourceView):
    @Operation(summary='404')
    def get(self):
        raise NotFound

    @Operation(summary='参数错误')
    def post(self, query=Query(dict(a=schemas.Integer()))):
        pass

    @Operation(summary='自定义错误')
    def delete(self):
        raise MyError


def test_custom_404(client):
    response = client.get(Res.reverse())
    assert response.status_code == 200
    assert response.json() == {'errorCode': 404}


def test_custom_request_args_error(client):
    response = client.post(Res.reverse())
    assert response.status_code == 422
    assert response.json() == {'err': {'a': ['这个字段是必需的']}}


def test_custom_error(client):
    response = client.delete(Res.reverse())
    assert response.status_code == 200
    assert response.content == b'custom error'
