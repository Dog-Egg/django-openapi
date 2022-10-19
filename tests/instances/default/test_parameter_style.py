"""参数样式"""
from django_openapi import Operation
from django_openapi.parameters import Query, Style
from django_openapi.schema import schemas
from django_openapi.urls import reverse
from tests.utils import TestResource, ResourceView

__url__ = 'https://swagger.io/specification/#style-values'


@TestResource
class A(ResourceView):
    @staticmethod
    @Operation(summary='Query')
    def get(q=Query(dict(
        a=schemas.List(schemas.Integer, required=False, description='form-true'),
        a2=schemas.List(schemas.Integer, required=False, description='form-false', style=Style(explode=False)),
        b=schemas.List(schemas.Integer, required=False, description='pipeDelimited-false',
                       style=Style(Style.PIPE_DELIMITED)),
        c=schemas.List(schemas.Integer, required=False, description='spaceDelimited-false',
                       style=Style(Style.SPACE_DELIMITED)),
    ))):
        return q


def test_query_form_true_array(client):
    resp = client.get(f'{reverse(A)}?a=1&a=20&a=301')
    assert resp.status_code == 200
    assert resp.json() == {'a': [1, 20, 301]}


def test_query_form_false_array(client):
    resp = client.get(f'{reverse(A)}?a2=1,2,30')
    assert resp.json() == {'a2': [1, 2, 30]}


def test_query_pipe_false_array(client):
    assert client.get(f'{reverse(A)}?b=1|2|30').json() == {'b': [1, 2, 30]}


def test_query_space_false_array(client):
    assert client.get(f'{reverse(A)}?c=1 2 30').json() == {'c': [1, 2, 30]}
    assert client.get(f'{reverse(A)}?c=1%202%2030').json() == {'c': [1, 2, 30]}


@TestResource('/simple-false/{args}/', path_parameters=dict(args=schemas.List(schemas.Integer)))
class PathSimpleFalse(ResourceView):
    @Operation(summary='Path')
    def get(self):
        return self.pathargs


def test_path_simple_false_array(client):
    assert client.get(f'{reverse(PathSimpleFalse, kwargs=dict(args="1,2,30"))}').json() == {'args': [1, 2, 30]}
    assert client.get(f'{reverse(PathSimpleFalse, kwargs=dict(args="1"))}').json() == {'args': [1]}
