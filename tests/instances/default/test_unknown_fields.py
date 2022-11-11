import pytest

from django_openapi.parameters import Query
from django_openapi.schema import schemas
from django_openapi.schema.exceptions import ValidationError
from django_openapi.urls import reverse
from tests.utils import TestResource


class Schema(schemas.Model):
    id = schemas.Integer(read_only=True)
    name = schemas.String()  # type: ignore


def test_error_param():
    with pytest.raises(ValueError, match="^unknown_fields must be one of 'include', 'exclude', 'error'.$"):
        Schema(unknown_fields='xxx')


def test_include():
    result = Schema(unknown_fields='include').deserialize({'name': 'Lee', 'address': '小胡同'})
    assert result == {'name': 'Lee', 'address': '小胡同'}


def test_error():
    with pytest.raises(ValidationError):
        try:
            Schema(unknown_fields='error').deserialize({'name': 'Lee', 'address': '小胡同', 'id': 1})
        except ValidationError as exc:
            assert exc.format_errors() == {'address': ['unknown field.'], 'id': ['unknown field.']}
            raise

    assert Schema(unknown_fields='error').deserialize({'name': 'Lee'}) == {'name': 'Lee'}


# test Meta

class SchemaA(schemas.Model):
    name = schemas.String()  # type: ignore

    class Meta:
        unknown_fields = 'error'


class SchemaB(SchemaA):
    age = schemas.Integer()


def test_meta_unknown_fields():
    with pytest.raises(ValidationError):
        try:
            SchemaB().deserialize({'name': 'Lee', 'age': 18, 'address': '北京'})
        except ValidationError as exc:
            assert exc.format_errors() == {'address': ['unknown field.']}
            raise


def test_unknown_fields_inherit():
    assert SchemaA.partial()._metadata['unknown_fields'] == 'error'


@TestResource
class API:
    @staticmethod
    def get(query=Query(schemas.Model.from_dict({'a': schemas.Integer()}, meta={'unknown_fields': 'error'}))):
        return query

    @staticmethod
    def post(query=Query(schemas.Model.from_dict({'a': schemas.Integer()}, meta={'unknown_fields': 'include'}))):
        return query


def test_query_string_unknown_fields_error(client):
    """测试 StyleParser.parse 不能直接清理数据，不然 QuerySchema 等无法使用 unknown_fields"""
    response = client.get(reverse(API), data={'a': 1, 'b': [2, 3]})
    assert response.request['QUERY_STRING'] == 'a=1&b=2&b=3'
    assert response.json() == {'errors': {'b': ['unknown field.']}}


def test_query_string_unknown_fields_include(client):
    response = client.post(reverse(API) + '?a=1&b=2&b=3')
    assert response.json() == {'a': 1, 'b': ['2', '3']}
