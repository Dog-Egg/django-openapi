import datetime

import pytest

from openapi.schema import schemas, validators
from openapi.schema.exceptions import DeserializationError


def test_inherit():
    """Model 单继承"""

    class Person(schemas.Model):
        name = schemas.String()
        birthday = schemas.Date()

    class Student(Person):
        grade = schemas.String()

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
    """Model 多继承"""

    class A(schemas.Model):
        a = schemas.Integer()
        b = schemas.Integer()

    class B(schemas.Model):
        a = schemas.String()

    class C(A, B):
        b = schemas.String()
        c = schemas.Integer()

    assert C._fields.__len__() == 3
    assert C().deserialize({'a': '1', 'b': '1', 'c': '1'}) == {'a': 1, 'b': '1', 'c': 1}


def test_field_visibility():
    """Model 字段可见性"""

    class SchemaA(schemas.Model):
        foo = schemas.String()

    assert isinstance(SchemaA.foo, schemas.Schema)  # 类可访问

    # 实例不可访问
    with pytest.raises(AttributeError, match="""^'SchemaA' object has no attribute 'foo'$"""):
        assert SchemaA().foo


def test_field_name():
    with pytest.raises(ValueError, match="Field name cannot start with '_'"):
        class SchemaA(schemas.Model):
            _name = schemas.String()


def test_field_conflict():
    """Schema 字段和方法字段冲突

    目前不清楚怎么处理合适
    """

    class SchemaA(schemas.Model):
        deserialize = schemas.Integer()  # 和内置方法重名
        Meta = schemas.Integer()  # 和内置属性重名

    assert SchemaA.deserialize == schemas.Model.deserialize
    assert isinstance(SchemaA.Meta, schemas.Schema)
    assert SchemaA._metadata
    # noinspection PyCallingNonCallable
    assert SchemaA().deserialize({'deserialize': '1', 'Meta': '2'}) == {'deserialize': 1, 'Meta': 2}


def test_deserialize():
    class SchemaA(schemas.Model):
        d = schemas.Integer()

    class SchemaB(schemas.Model):
        a = schemas.String()
        b = schemas.Integer()
        c = SchemaA()

    assert SchemaB().deserialize({'a': '1', 'b': '2', 'c': {'d': '3'}}) == {'a': '1', 'b': 2, 'c': {'d': 3}}


def test_deserialize_error():
    class Schema3(schemas.Model):
        a3 = schemas.Integer()

    class Schema2(schemas.Model):
        a2 = schemas.Integer()
        b2 = schemas.List(schemas.Integer)
        c2 = schemas.List(Schema3())

    class Schema1(schemas.Model):
        a1 = schemas.Integer()
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
    class SchemaA(schemas.Model):
        a = schemas.Integer(required=False)

    assert 'a' not in SchemaA().deserialize({})

    class SchemaB(schemas.Model):
        a = schemas.Integer(required=True)

    with pytest.raises(DeserializationError):
        try:
            SchemaB().deserialize({})
        except DeserializationError as e:
            assert e.message == {'a': ['这个字段是必需的']}
            raise

    assert schemas.Integer().required
    assert not schemas.Integer(default=1).required


def test_field_default():
    class SchemaA(schemas.Model):
        a = schemas.Integer(default=1)

    assert SchemaA().deserialize({}) == {'a': 1}


def test_field_attr_alias():
    class SchemaA(schemas.Model):
        foo = schemas.Integer(alias='k', attr='a')

    assert SchemaA().deserialize({'k': '1'}) == {'a': 1}
    assert SchemaA().serialize({'a': 1}) == {'k': 1}


def test_validate_error():
    class Schema1(schemas.Model):
        a = schemas.String(validators=[validators.Length(min=6), validators.Length(max=2)])

    with pytest.raises(DeserializationError):
        try:
            Schema1().deserialize({'a': '123'})
        except DeserializationError as e:
            assert e.message == {'a': ['长度最小为 6', '长度最大为 2']}
            raise
