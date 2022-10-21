"""Schemas"""
import datetime
from decimal import Decimal

import pytest

from django_openapi.parameters import Query, Body
from django_openapi.schema import schemas
from django_openapi.schema.exceptions import ValidationError
from django_openapi.utils.functional import make_instance
from tests.utils import TestResource, ResourceView


def test_serialize_and_deserialize():
    def serialize_ok(schema, input_value, output_value):
        value = make_instance(schema).serialize(input_value)
        assert value == output_value and type(value) is type(output_value)

    def deserialize_ok(schema, input_value, output_value):
        value = make_instance(schema).deserialize(input_value)
        assert value == output_value and type(value) is type(output_value)

    def deserialize_err(schema, value, err_msg):
        with pytest.raises(ValidationError, match=err_msg):
            make_instance(schema).deserialize(value)

    # string
    serialize_ok(schemas.String, '1', '1')
    serialize_ok(schemas.String, 1, '1')
    serialize_ok(schemas.String(strip=True), ' a', ' a')  # strip 不会应用于序列化

    deserialize_ok(schemas.String, '1', '1')
    deserialize_ok(schemas.String(strip=True), ' a', 'a')
    deserialize_ok(schemas.String, ' a', ' a')  # 默认 strip=False

    deserialize_err(schemas.String, 1, '必须是字符串')  # string 严格反序列，防止后端无法区分 None 和 "None" 等

    deserialize_ok(schemas.String(whitespace=True), '', '')
    deserialize_ok(schemas.String(whitespace=True), ' \n', ' \n')
    deserialize_ok(schemas.String(whitespace=True, strip=True), ' \n', '')
    deserialize_err(schemas.String(whitespace=False), '', 'cannot be a whitespace string')
    deserialize_err(schemas.String(whitespace=False), ' ', 'cannot be a whitespace string')
    deserialize_err(schemas.String(whitespace=False, strip=True), ' ', 'cannot be a whitespace string')

    # integer
    serialize_ok(schemas.Integer, 1, 1)
    serialize_ok(schemas.Integer, Decimal('1'), 1)
    serialize_ok(schemas.Integer, Decimal('1.1'), 1)
    serialize_ok(schemas.Integer, '1', 1)
    serialize_ok(schemas.Integer, 1.1, 1)

    deserialize_ok(schemas.Integer, 1, 1)
    deserialize_ok(schemas.Integer, '1', 1)
    deserialize_ok(schemas.Integer, 1.0, 1)
    deserialize_ok(schemas.Integer, '1.0', 1)

    deserialize_err(schemas.Integer, 'a', '不是一个整数'),
    deserialize_err(schemas.Integer, '1.1', '不是一个整数'),
    deserialize_err(schemas.Integer, 1.1, '不是一个整数'),

    # float
    serialize_ok(schemas.Float, 1.0, 1.0)
    serialize_ok(schemas.Float, 1, 1.0)
    serialize_ok(schemas.Float, 1.1, 1.1)
    serialize_ok(schemas.Float, Decimal('1'), 1.0)
    serialize_ok(schemas.Float, Decimal('1.1'), 1.1)
    serialize_ok(schemas.Float, '1', 1.0)
    serialize_ok(schemas.Float, '1.1', 1.1)

    deserialize_ok(schemas.Float, '1', 1.0)
    deserialize_ok(schemas.Float, 1, 1.0)
    deserialize_ok(schemas.Float, 1.1, 1.1)
    deserialize_ok(schemas.Float, '1.1', 1.1)

    deserialize_err(schemas.Float, 'a', '不是一个浮点数')

    # list
    serialize_ok(schemas.List(schemas.String), 'abc', ['a', 'b', 'c'])
    serialize_ok(schemas.List(schemas.List(schemas.Integer())), [[1, 2, '3']], [[1, 2, 3]])

    deserialize_ok(schemas.List(schemas.Integer()), ['1', '1.0', 1], [1, 1, 1])
    deserialize_ok(schemas.List(schemas.List(schemas.Integer())), ['123'], [[1, 2, 3]])

    deserialize_err(schemas.List(schemas.Integer), 123, '不是一个可迭代对象'),

    # dict
    serialize_ok(schemas.Dict(), {'a': 1}, {'a': 1})
    serialize_ok(schemas.Dict(schemas.Integer), {'a': '0'}, {'a': 0})
    serialize_ok(schemas.Dict(key=schemas.Integer), {'0': '0'}, {0: '0'})

    deserialize_ok(schemas.Dict(), {'a': 1}, {'a': 1})
    deserialize_ok(schemas.Dict(schemas.Integer), {'a': '0'}, {'a': 0})
    deserialize_ok(schemas.Dict(key=schemas.Integer), {'0': '0'}, {0: '0'})

    deserialize_err(schemas.Dict(), 1, 'not a valid dict object.')
    deserialize_err(schemas.Dict(schemas.Integer), {'a': 'a'}, 'The value 不是一个整数')
    deserialize_err(schemas.Dict(key=schemas.Integer), {'a': 'a'}, 'The key 不是一个整数')

    # boolean
    serialize_ok(schemas.Boolean, True, True)
    serialize_ok(schemas.Boolean, False, False)
    serialize_ok(schemas.Boolean, 1, True)
    serialize_ok(schemas.Boolean, 0, False)
    serialize_ok(schemas.Boolean, ' ', True)
    serialize_ok(schemas.Boolean, '', False)

    deserialize_ok(schemas.Boolean, '1', True)
    deserialize_ok(schemas.Boolean, '0', False)
    deserialize_ok(schemas.Boolean, 1, True)
    deserialize_ok(schemas.Boolean, 0, False)
    deserialize_ok(schemas.Boolean, 'True', True)
    deserialize_ok(schemas.Boolean, 'true', True)
    deserialize_ok(schemas.Boolean, 'false', False)
    deserialize_ok(schemas.Boolean, False, False)

    deserialize_err(schemas.Boolean, 'tRue', '不是一个有效布尔值'),
    deserialize_err(schemas.Boolean, 2, '不是一个有效布尔值'),

    # date
    serialize_ok(schemas.Date, datetime.date(2022, 7, 4), '2022-07-04')
    serialize_ok(schemas.Date(fmt='%Y%m%d'), datetime.date(2022, 5, 1), '20220501')

    deserialize_ok(schemas.Date, '2022-05-01', datetime.date(2022, 5, 1))
    deserialize_ok(schemas.Date, '20220501', datetime.date(2022, 5, 1))
    deserialize_ok(schemas.Date(dfmt='%Y/%m/%d'), '2022/05/01', datetime.date(2022, 5, 1))

    deserialize_err(schemas.Date, '2022-13-05', 'Not a valid date string.')
    deserialize_err(schemas.Date, '2022-5-1', 'Not a valid date string.')
    deserialize_err(schemas.Date, 20220501, 'Not a valid date string.')
    deserialize_err(schemas.Date, '2022/05/01', 'Not a valid date string.')

    # datetime
    serialize_ok(schemas.Datetime, datetime.datetime(2022, 5, 1), '2022-05-01T00:00:00')
    serialize_ok(schemas.Datetime, datetime.datetime(2022, 5, 1, tzinfo=datetime.timezone.utc),
                 '2022-05-01T00:00:00+00:00')
    serialize_ok(schemas.Datetime(fmt='%Y%m%d %H:%M:%S'), datetime.datetime(2022, 5, 1), '20220501 00:00:00')

    deserialize_ok(schemas.Datetime, '2022-05-01', datetime.datetime(2022, 5, 1))
    deserialize_ok(schemas.Datetime, '20220501', datetime.datetime(2022, 5, 1))
    deserialize_ok(schemas.Datetime(dfmt='%Y/%m/%d'), '2022/05/01', datetime.datetime(2022, 5, 1))
    deserialize_ok(schemas.Datetime(with_timezone=False), '2022-10-20T10:16:02',
                   datetime.datetime(2022, 10, 20, 10, 16, 2))
    deserialize_ok(schemas.Datetime(with_timezone=True), '2022-10-20T10:16:02Z',
                   datetime.datetime(2022, 10, 20, 10, 16, 2, tzinfo=datetime.timezone.utc))
    deserialize_ok(schemas.Datetime(with_timezone=None), '2022-10-20T10:16:02Z',
                   datetime.datetime(2022, 10, 20, 10, 16, 2, tzinfo=datetime.timezone.utc))
    deserialize_ok(schemas.Datetime(with_timezone=None), '2022-10-20T10:16:02',
                   datetime.datetime(2022, 10, 20, 10, 16, 2))

    deserialize_err(schemas.Datetime, 20220501, 'Not a valid datetime string')
    deserialize_err(schemas.Datetime, '2022/05/01', 'Not a valid datetime string')
    deserialize_err(schemas.Datetime(with_timezone=False), '2022-10-20T10:16:02Z',
                    'not support timezone-aware datetime.')
    deserialize_err(schemas.Datetime(with_timezone=True), '2022-10-20T10:16:02',
                    'not support timezone-naive datetime.')

    # file

    # any
    serialize_ok(schemas.Any, 1, 1)
    serialize_ok(schemas.Any, '1', '1')
    serialize_ok(schemas.Any, None, None)

    deserialize_ok(schemas.Any, 1, 1)
    deserialize_ok(schemas.Any, '1', '1')
    deserialize_ok(schemas.Any, None, None)


def test_schema_to_spec(to_spec):
    assert to_spec(schemas.String) == dict(type='string')
    assert to_spec(schemas.Any) == {'nullable': True}
    assert to_spec(schemas.Any(nullable=False)) == {}
    assert to_spec(schemas.Password) == {'format': 'password', 'type': 'string', 'writeOnly': True}


@pytest.mark.parametrize('schema', [
    schemas.String,
    schemas.Integer,
    schemas.Float,
    schemas.List,
    schemas.Boolean,
    schemas.Date,
    schemas.Datetime,
    schemas.Model,
    schemas.Any,
    schemas.File,
    schemas.Dict,
])
def test_nullable(schema):
    assert schema(nullable=True).serialize(None) is None

    assert schema(nullable=True).deserialize(None) is None

    with pytest.raises(ValueError, match='The value cannot be None'):
        schema(nullable=False).serialize(None)

    with pytest.raises(ValidationError, match='The value cannot be null'):
        schema(nullable=False).deserialize(None)


@TestResource
class ResA(ResourceView):
    @staticmethod
    def post(q=Query(dict(
        a=schemas.String(required=False),
        b=schemas.Integer(required=False),
        c=schemas.Float(required=False),
        d=schemas.Boolean(required=False),
        e=schemas.Date(required=False, example='2022-10-01'),
        f=schemas.Datetime(required=False, example='2022-10-01 08:00:00'),
        i=schemas.List(required=False),
        any=schemas.Any(required=False),
    )), b=Body(dict(j=schemas.Dict(schemas.Integer, schemas.Integer, required=False, example={'foo': 1})))):
        return dict(q=q, b=b)
