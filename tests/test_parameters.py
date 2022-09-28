"""请求参数"""

from django.http import SimpleCookie

from django_openapi import Operation
from django_openapi.exceptions import NotFound
from django_openapi.parameters import Query, Header, Cookie
from django_openapi.schema import schemas
from tests.utils import TestResource, ResourceView


@TestResource(
    '/path/{id}',
    path_parameters=dict(id=schemas.Integer()),
)
class PathParameter1(ResourceView):
    @Operation(
        summary='path参数',
        description='假设 id 大于等于0，错误返回404'
    )
    def get(self):
        if self.pathargs['id'] < 0:
            raise NotFound
        return self.pathargs


@TestResource(
    '/path/{path}',
    path_parameters=dict(path=schemas.Path()),
)
class PathParameter2(ResourceView):
    @Operation(
        summary='path参数2 - Path Schema类型',
    )
    def get(self):
        return self.pathargs


def test_path_parameter(client):
    response = client.get(PathParameter1.reverse(id=8))
    assert response.json() == {'id': 8}


def test_path_parameter_404(client):
    assert client.get(PathParameter1.reverse(id=-1)).status_code == 404
    assert client.get(PathParameter1.reverse(id='a')).status_code == 404


def test_path_parameter_with_path_schema(client):
    response = client.get(PathParameter2.reverse(path='xx/xxx'))
    assert response.json() == {'path': 'xx/xxx'}


@TestResource
class Parameter1(ResourceView):
    @Operation(
        summary='query参数'
    )
    def get(self, query=Query(dict(a=schemas.String(required=False), b=schemas.Integer()))):
        return query

    @Operation(
        summary='使用多个Query对象'
    )
    def post(
            self,
            q1=Query(dict(a=schemas.Integer(required=False))),
            q2=Query(dict(b=schemas.String(required=False))),
    ):
        return dict(q1=q1, q2=q2)

    @Operation(
        summary='header参数'
    )
    def put(self, h1=Header(dict(h=schemas.String()))):
        return h1

    @Operation(
        summary='cookie参数'
    )
    def patch(self, c1=Cookie(dict(c=schemas.String()))):
        return c1


def test_query_parameter(client):
    response = client.get(Parameter1.reverse(), data={'a': 1, 'b': 2})
    assert response.json() == {'a': '1', 'b': 2}


def test_query_parameter_400(client):
    response = client.get(Parameter1.reverse())
    assert response.status_code == 400
    assert response.json() == {'errors': {'b': ['这个字段是必需的']}}


def test_multi_query(client):
    response = client.post(f'{Parameter1.reverse()}?a=1&b=2')
    assert response.json() == {'q1': {'a': 1}, 'q2': {'b': '2'}}


def test_header_parameter(client):
    response = client.put(Parameter1.reverse(), HTTP_H='h1')
    assert response.json() == {'h': 'h1'}


def test_cookie_parameter(client):
    client.cookies = SimpleCookie({'c': 'c2'})
    assert client.patch(Parameter1.reverse()).json() == {'c': 'c2'}
