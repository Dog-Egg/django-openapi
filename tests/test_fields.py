import datetime

import pytest

from openapi.schemax import fields
from openapi.schemax.exceptions import SerializationError, DeserializationError
from openapi.utils import make_instance


@pytest.mark.parametrize(
    'field,input_value,output_value',
    [
        # string
        (fields.String, '1', '1'),
        (fields.String(), ' a', ' a'),
        (fields.String(strip=True), ' a', ' a'),  # strip 不会应用于序列化

        # integer
        (fields.Integer, 1, 1),

        # float
        (fields.Float, 1.0, 1.0),

        # list
        (fields.List(fields.String), 'abc', ['a', 'b', 'c']),
        (fields.List(fields.List(fields.Integer())), [[1, 2, 3]], [[1, 2, 3]]),

        # boolean
        (fields.Boolean, True, True),
        (fields.Boolean, False, False),

        # date
        (fields.Date, datetime.date(2022, 7, 4), '2022-07-04')
    ]
)
def test_serialize(field, input_value, output_value):
    """序列化成功测试"""
    value = make_instance(field).serialize(input_value)
    assert value == output_value
    assert type(value) is type(output_value)


@pytest.mark.parametrize(
    'field,value,error_message',
    [
        # string
        (fields.String, 1, '必须是字符串'),
        (fields.String, None, '必须是字符串'),

        # integer
        (fields.Integer, '1', '不是一个整数'),
        (fields.Integer, 1.1, '不是一个整数'),
        (fields.Integer, 'a', '不是一个整数'),
        (fields.Integer, None, '不是一个整数'),

        # float
        (fields.Float, 1, '不是一个浮点数'),
        (fields.Float, '1.1', '不是一个浮点数'),
        (fields.Float, 'a', '不是一个浮点数'),
        (fields.Float, None, '不是一个浮点数'),

        # list
        (fields.List(fields.Integer), 123, '不是一个可迭代对象'),
        (fields.List(fields.Integer), None, '不是一个可迭代对象'),

        # boolean
        (fields.Boolean, 1, '不是一个有效布尔值'),
        (fields.Boolean, '1', '不是一个有效布尔值'),
        (fields.Boolean, None, '不是一个有效布尔值'),

        # date
        (fields.Date, '2022-07-04', '不是一个日期对象'),
        (fields.Date, None, '不是一个日期对象'),
    ]
)
def test_serialize_error(field, value, error_message):
    """序列化错误测试"""
    with pytest.raises(SerializationError, match=error_message):
        make_instance(field).serialize(value)


@pytest.mark.parametrize(
    'field,input_value,output_value',
    [
        # string
        (fields.String, '1', '1'),
        (fields.String(strip=True), ' a', 'a'),
        (fields.String, ' a', ' a'),

        # integer
        (fields.Integer, 1, 1),
        (fields.Integer, '1', 1),
        (fields.Integer, 1.0, 1),
        (fields.Integer, '1.0', 1),

        # float
        (fields.Float, '1', 1.0),
        (fields.Float, 1, 1.0),
        (fields.Float, 1.1, 1.1),
        (fields.Float, '1.1', 1.1),

        # list
        (fields.List(fields.Integer()), ['1', '1.0', 1], [1, 1, 1]),
        (fields.List(fields.List(fields.Integer())), ['123'], [[1, 2, 3]]),

        # boolean
        (fields.Boolean, '1', True),
        (fields.Boolean, '0', False),
        (fields.Boolean, 1, True),
        (fields.Boolean, 0, False),
        (fields.Boolean, 'True', True),
        (fields.Boolean, 'true', True),
        (fields.Boolean, 'false', False),
        (fields.Boolean, False, False),

        # date
        (fields.Date, '2022-05-01', datetime.date(2022, 5, 1)),
    ]
)
def test_deserialize(field, input_value, output_value):
    """反序列成功测试"""
    value = make_instance(field).deserialize(input_value)
    assert value == output_value
    assert type(value) is type(output_value)


@pytest.mark.parametrize(
    'field,value,error_message',
    [
        # string
        (fields.String, 1, '必须是字符串'),
        (fields.String, None, '必须是字符串'),

        # integer
        (fields.Integer, 'a', '不是一个整数'),
        (fields.Integer, '1.1', '不是一个整数'),
        (fields.Integer, 1.1, '不是一个整数'),
        (fields.Integer, None, '不是一个整数'),

        # float
        (fields.Float, 'a', '不是一个浮点数'),
        (fields.Float, None, '不是一个浮点数'),

        # list
        (fields.List(fields.Integer), 123, '不是一个可迭代对象'),
        (fields.List(fields.Integer), None, '不是一个可迭代对象'),

        # boolean
        (fields.Boolean, 'tRue', '不是一个有效布尔值'),
        (fields.Boolean, 2, '不是一个有效布尔值'),
        (fields.Boolean, None, '不是一个有效布尔值'),

        # date
        (fields.Date, '2022-13-05', '不是一个有效的日期值'),
        (fields.Date, '2022-5-1', '不是一个有效的日期值'),
        (fields.Date, '20220501', '不是一个有效的日期值'),
        (fields.Date, 20220501, '不是一个有效的日期值'),
        (fields.Date, None, '不是一个有效的日期值'),
    ]
)
def test_deserialize_error(field, value, error_message):
    """反序列化错误测试"""
    with pytest.raises(DeserializationError, match=error_message):
        make_instance(field).deserialize(value)
