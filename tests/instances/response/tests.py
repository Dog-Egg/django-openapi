from django_openapi import Operation
from django_openapi.exceptions import NotFound
from django_openapi.parameters import Query
from django_openapi.schema import schemas
from django_openapi.urls import reverse
from .exceptions import MyError
from tests.utils import TestResource, ResourceView


@TestResource
class API(ResourceView):
    class ResponseSchema(schemas.Model):
        field1 = schemas.String()
        field2 = schemas.Integer()

    @Operation(
        summary='status 200',
        response_schema=ResponseSchema,
    )
    def get(self):
        return dict(field1='string', field2=0)

    @Operation(summary='status 404')
    def put(self):
        raise NotFound

    @Operation(summary='参数错误')
    def post(self, query=Query(dict(a=schemas.Integer()))):
        pass

    @Operation(summary='抛出自定义异常')
    def delete(self):
        raise MyError


def test_custom_404(client):
    response = client.put(reverse(API))
    assert response.status_code == 200
    assert response.json() == {'code': 404}


def test_custom_request_args_error(client):
    response = client.post(reverse(API))
    assert response.status_code == 422
    assert response.json() == {'code': 400, 'errors': {'a': ['这个字段是必需的']}}


def test_custom_error(client):
    response = client.delete(reverse(API))
    assert response.status_code == 200
    assert response.json() == {'code': 1, 'message': 'error'}
