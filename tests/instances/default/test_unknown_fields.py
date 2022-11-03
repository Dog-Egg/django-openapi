import pytest

from django_openapi.schema import schemas
from django_openapi.schema.exceptions import ValidationError


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
