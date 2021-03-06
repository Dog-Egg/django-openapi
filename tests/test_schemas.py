import datetime
from decimal import Decimal

import pytest

from openapi.schema import schemas
from openapi.schema.exceptions import SerializationError, DeserializationError
from openapi.schema.schemas import SchemaABC
from openapi.schema.validators import RangeValidator
from openapi.utils import make_instance


@pytest.mark.parametrize(
    'schema,input_value,output_value',
    [
        # string
        (schemas.String, '1', '1'),
        (schemas.String(), ' a', ' a'),
        (schemas.String(strip=True), ' a', ' a'),  # strip 不会应用于序列化

        # integer
        (schemas.Integer, 1, 1),
        (schemas.Integer, Decimal('1'), 1),

        # float
        (schemas.Float, 1.0, 1.0),
        (schemas.Float, 1, 1.0),
        (schemas.Float, 1.1, 1.1),
        (schemas.Float, Decimal('1'), 1.0),
        (schemas.Float, Decimal('1.1'), 1.1),

        # list
        (schemas.List(schemas.String), 'abc', ['a', 'b', 'c']),
        (schemas.List(schemas.List(schemas.Integer())), [[1, 2, 3]], [[1, 2, 3]]),

        # boolean
        (schemas.Boolean, True, True),
        (schemas.Boolean, False, False),

        # date
        (schemas.Date, datetime.date(2022, 7, 4), '2022-07-04')
    ]
)
def test_serialize(schema, input_value, output_value):
    """序列化成功测试"""
    value = make_instance(schema).serialize(input_value)
    assert value == output_value
    assert type(value) is type(output_value)


@pytest.mark.parametrize(
    'schema,value,error_message',
    [
        # string
        (schemas.String, 1, '必须是字符串'),

        # integer
        (schemas.Integer, '1', '不是一个整数'),
        (schemas.Integer, 1.1, '不是一个整数'),
        (schemas.Integer, 'a', '不是一个整数'),
        (schemas.Integer, Decimal('1.1'), '不是一个整数'),

        # float
        (schemas.Float, '1.1', '不是一个浮点数'),
        (schemas.Float, 'a', '不是一个浮点数'),

        # list
        (schemas.List(schemas.Integer), 123, '不是一个可迭代对象'),

        # boolean
        (schemas.Boolean, 1, '不是一个有效布尔值'),
        (schemas.Boolean, '1', '不是一个有效布尔值'),

        # date
        (schemas.Date, '2022-07-04', '不是一个日期对象'),
    ]
)
def test_serialize_error(schema, value, error_message):
    """序列化错误测试"""
    with pytest.raises(SerializationError, match=error_message):
        make_instance(schema).serialize(value)


@pytest.mark.parametrize(
    'schema,input_value,output_value',
    [
        # string
        (schemas.String, '1', '1'),
        (schemas.String(strip=True), ' a', 'a'),
        (schemas.String, ' a', ' a'),

        # integer
        (schemas.Integer, 1, 1),
        (schemas.Integer, '1', 1),
        (schemas.Integer, 1.0, 1),
        (schemas.Integer, '1.0', 1),

        # float
        (schemas.Float, '1', 1.0),
        (schemas.Float, 1, 1.0),
        (schemas.Float, 1.1, 1.1),
        (schemas.Float, '1.1', 1.1),

        # list
        (schemas.List(schemas.Integer()), ['1', '1.0', 1], [1, 1, 1]),
        (schemas.List(schemas.List(schemas.Integer())), ['123'], [[1, 2, 3]]),

        # boolean
        (schemas.Boolean, '1', True),
        (schemas.Boolean, '0', False),
        (schemas.Boolean, 1, True),
        (schemas.Boolean, 0, False),
        (schemas.Boolean, 'True', True),
        (schemas.Boolean, 'true', True),
        (schemas.Boolean, 'false', False),
        (schemas.Boolean, False, False),

        # date
        (schemas.Date, '2022-05-01', datetime.date(2022, 5, 1)),
    ]
)
def test_deserialize(schema, input_value, output_value):
    """反序列成功测试"""
    schema: SchemaABC = make_instance(schema)
    value = schema.deserialize(input_value)
    assert value == output_value
    assert type(value) is type(output_value)


@pytest.mark.parametrize(
    'schema,value,error_message',
    [
        # string
        (schemas.String, 1, '必须是字符串'),

        # integer
        (schemas.Integer, 'a', '不是一个整数'),
        (schemas.Integer, '1.1', '不是一个整数'),
        (schemas.Integer, 1.1, '不是一个整数'),

        # float
        (schemas.Float, 'a', '不是一个浮点数'),

        # list
        (schemas.List(schemas.Integer), 123, '不是一个可迭代对象'),

        # boolean
        (schemas.Boolean, 'tRue', '不是一个有效布尔值'),
        (schemas.Boolean, 2, '不是一个有效布尔值'),

        # date
        (schemas.Date, '2022-13-05', '不是一个有效的日期值'),
        (schemas.Date, '2022-5-1', '不是一个有效的日期值'),
        (schemas.Date, '20220501', '不是一个有效的日期值'),
        (schemas.Date, 20220501, '不是一个有效的日期值'),
    ]
)
def test_deserialize_error(schema, value, error_message):
    """反序列化错误测试"""
    with pytest.raises(DeserializationError, match=error_message):
        schema: SchemaABC = make_instance(schema)
        schema.deserialize(value)


@pytest.mark.parametrize('schema', [
    schemas.String,
    schemas.Integer,
    schemas.Float,
    schemas.List,
    schemas.Boolean,
    schemas.Date,
    schemas.Model,
    schemas.Any,
])
def test_nullable(schema):
    assert schema(nullable=True).serialize(None) is None
    assert schema(nullable=True).deserialize(None) is None

    with pytest.raises(SerializationError, match='不能为 null'):
        schema(nullable=False).serialize(None)
    with pytest.raises(DeserializationError, match='不能为 None'):
        schema(nullable=False).deserialize(None)


def test_number_range():
    assert schemas.Integer(gte=1).deserialize('1') == 1

    with pytest.raises(DeserializationError, match='^The value must be greater than 1$'):
        schemas.Integer(gt=1).deserialize(1)

    with pytest.raises(DeserializationError,
                       match="['The value must be less than 1', 'The value must be greater than 1']"):
        schemas.Integer(gt=1, validators=[RangeValidator(lt=1)]).deserialize(1)


def test_number_multiple():
    assert schemas.Integer(multiple_of=3).deserialize('9') == 9

    with pytest.raises(DeserializationError, match='^The value must be a multiple of 4$'):
        schemas.Integer(multiple_of=4).deserialize(9)

    # multiple_of=0.01 可用于如"价格"的表示
    assert schemas.Float(multiple_of=0.01, gte=0).deserialize(1.01) == 1.01
    assert schemas.Float(multiple_of=0.01).deserialize(1) == 1

    with pytest.raises(DeserializationError, match='^The value must be a multiple of 0.01$'):
        schemas.Float(multiple_of=0.01).deserialize(1.002)


def test_field_blank():
    # 不可为空
    class Schema1(schemas.Model):
        f1 = schemas.String()
        f2 = schemas.Integer(required=False)

    try:
        Schema1().deserialize({'f1': '', 'f2': ' '})
    except DeserializationError as exc:
        assert exc.error == {'f1': ['字段不能是空白的']}

    # 可为空
    class Schema2(schemas.Model):
        f1 = schemas.String(allow_blank=True)

    assert Schema2().deserialize({'f1': ' '}) == {'f1': ' '}

    # 可为空但是类型错误
    class Schema3(schemas.Model):
        f1 = schemas.Integer(allow_blank=True)

    try:
        Schema3().deserialize({'f1': ''})
    except DeserializationError as exc:
        assert exc.error == {'f1': ['不是一个整数']}

    # 实际应用
    class Search(schemas.Model):
        arg1 = schemas.Integer(required=False)
        arg2 = schemas.Integer(required=False)

    assert Search().deserialize({'arg1': '', 'arg2': '123'}) == {'arg2': 123}
