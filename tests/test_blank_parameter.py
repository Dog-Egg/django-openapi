"""空白请求参数"""
from django_openapi import Operation
from django_openapi.parameters import Query
from django_openapi.schema import schemas
from tests.utils import TestResource, ResourceView, itemgetter


@TestResource
class ResourceA(ResourceView):
    @Operation(
        summary='必要且允许为空'
    )
    def get(self, q=Query(dict(a=schemas.String(required=True, allow_blank=True)))):
        return q

    @Operation(
        summary='非必要且允许为空'
    )
    def post(self, q=Query(dict(a=schemas.String(required=False, allow_blank=True)))):
        return q

    @Operation(
        summary='非必要且不允许为空'
    )
    def put(self, q=Query(dict(a=schemas.String(required=False, allow_blank=False)))):
        return q

    @Operation(
        summary='必要且不允许为空'
    )
    def patch(self, q=Query(dict(a=schemas.String(required=True, allow_blank=False)))):
        return q


def test_required_and_allow_blank(client, get_oas):
    """必要且允许为空"""
    response = client.get(f'{ResourceA.reverse()}')
    assert response.status_code == 400
    assert response.json() == dict(errors=dict(a=['这个字段是必需的']))

    response = client.get(f'{ResourceA.reverse()}?a=')
    assert response.status_code == 200
    assert response.json() == {'a': ''}

    assert itemgetter(get_oas(), ['paths', ResourceA.reverse(), 'get', 'parameters', 0, 'allowEmptyValue']) is True


def test_not_required_and_allow_blank(client):
    """非必要且允许为空"""
    response = client.post(f'{ResourceA.reverse()}')
    assert response.json() == {}

    response = client.post(f'{ResourceA.reverse()}?a=')
    assert response.json() == {'a': ''}


def test_not_required_and_not_allow_blank(client, get_oas):
    """非必要且不允许为空"""
    response = client.put(f'{ResourceA.reverse()}')
    assert response.json() == {}

    response = client.put(f'{ResourceA.reverse()}?a=')
    assert response.json() == {}

    response = client.put(f'{ResourceA.reverse()}?a= ')
    assert response.json() == {}

    assert 'allowEmptyValue' not in itemgetter(get_oas(), ['paths', ResourceA.reverse(), 'put', 'parameters', 0])


def test_required_and_not_allow_blank(client):
    """必要且不允许为空"""
    resp = client.patch(f'{ResourceA.reverse()}')
    assert resp.json() == {'errors': {'a': ['这个字段是必需的']}}

    response = client.patch(f'{ResourceA.reverse()}?a=')
    assert response.json() == {'errors': {'a': ['字段不能是空白的']}}

    response = client.patch(f'{ResourceA.reverse()}?a= ')
    assert response.json() == {'errors': {'a': ['字段不能是空白的']}}
