import datetime

import pytest

from openapi.schemax import fields, validators
from openapi.schemax.exceptions import DeserializationError
from openapi.schemax.fields import Schema


def test_inherit():
    """Schema 单继承"""

    class Person(Schema):
        name = fields.String()
        birthday = fields.Date()

    class Student(Person):
        grade = fields.String()

    assert Student._fields.__len__() == 3
    assert Student().serialize({
        'name': '小明',
        'birthday': datetime.date(2001, 5, 1),
        'grade': '六年级'
    }) == {
               'name': '小明',
               'birthday': '2001-05-01',
               'grade': '六年级'
           }


def test_multiple_inherit():
    """Schema 多继承"""

    class A(Schema):
        a = fields.Integer()
        b = fields.Integer()

    class B(Schema):
        a = fields.String()

    class C(A, B):
        b = fields.String()
        c = fields.Integer()

    assert C._fields.__len__() == 3
    assert C().deserialize({'a': '1', 'b': '1', 'c': '1'}) == {'a': 1, 'b': '1', 'c': 1}


def test_field_visibility():
    """Schema 字段可见性"""

    class SchemaA(Schema):
        foo = fields.String()

    assert isinstance(SchemaA.foo, fields.Field)  # 类可访问

    # 实例不可访问
    with pytest.raises(AttributeError, match="""^'SchemaA' object has no attribute 'foo'$"""):
        assert SchemaA().foo


def test_field_conflict():
    """Schema 字段和方法字段冲突

    目前不清楚怎么处理合适
    """

    class SchemaA(Schema):
        deserialize = fields.Integer()  # 和内置方法重名
        _type = fields.Integer()  # 和内置属性重名

    assert SchemaA.deserialize == Schema.deserialize
    assert SchemaA._type == 'object'
    # noinspection PyCallingNonCallable
    assert SchemaA().deserialize({'deserialize': '1', '_type': '2'}) == {'deserialize': 1, '_type': 2}


def test_deserialize():
    class SchemaA(Schema):
        d = fields.Integer()

    class SchemaB(Schema):
        a = fields.String()
        b = fields.Integer()
        c = SchemaA()

    assert SchemaB().deserialize({'a': '1', 'b': '2', 'c': {'d': '3'}}) == {'a': '1', 'b': 2, 'c': {'d': 3}}


def test_deserialize_error():
    class Schema3(Schema):
        a3 = fields.Integer()

    class Schema2(Schema):
        a2 = fields.Integer()
        b2 = fields.List(fields.Integer)
        c2 = fields.List(Schema3())

    class Schema1(Schema):
        a1 = fields.Integer()
        b1 = Schema2()

    with pytest.raises(DeserializationError):
        try:
            Schema1().deserialize({
                'a1': 'a',
                'b1': {
                    'a2': 'a',
                    'b2': ['1', 'a'],
                    'c2': [{'a3': 'a'}]
                }
            })
        except DeserializationError as e:
            assert e.message == {
                'a1': ['不是一个整数'],
                'b1': {
                    'a2': ['不是一个整数'],
                    'b2': {
                        1: ['不是一个整数']
                    },
                    'c2': {0: [{'a3': ['不是一个整数']}]}
                }
            }
            raise


def test_field_required():
    class SchemaA(Schema):
        a = fields.Integer(required=False)

    assert 'a' not in SchemaA().deserialize({})

    class SchemaB(Schema):
        a = fields.Integer(required=True)

    with pytest.raises(DeserializationError):
        try:
            SchemaB().deserialize({})
        except DeserializationError as e:
            assert e.message == {'a': ['这个字段是必需的']}
            raise

    assert fields.Integer().required
    assert not fields.Integer(default=1).required


def test_field_default():
    class SchemaA(Schema):
        a = fields.Integer(default=1)

    assert SchemaA().deserialize({}) == {'a': 1}


def test_field_attr_key():
    class SchemaA(Schema):
        foo = fields.Integer(key='k', attr='a')

    assert SchemaA().deserialize({'k': '1'}) == {'a': 1}
    assert SchemaA().serialize({'a': 1}) == {'k': 1}


def test_validate_error():
    class Schema1(Schema):
        a = fields.String(validators=[validators.Length(min=6), validators.Length(max=2)])

    with pytest.raises(DeserializationError):
        try:
            Schema1().deserialize({'a': '123'})
        except DeserializationError as e:
            assert e.message == {'a': ['长度最小为 6', '长度最大为 2']}
            raise
