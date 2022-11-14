import datetime

import pytest

from django_openapi.schema import schemas, validators
from django_openapi.schema.exceptions import ValidationError


def test_inherit():
    """Model 单继承"""

    class Person(schemas.Model):
        name = schemas.String()
        birthday = schemas.Date()

    class Student(Person):
        grade = schemas.String()

    assert Student.fields.__len__() == 3
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

    assert C.fields.__len__() == 3
    assert C().deserialize({'a': '1', 'b': '1', 'c': '1'}) == {'a': 1, 'b': '1', 'c': 1}


def test_field_visibility():
    """Model 字段可见性"""

    class SchemaA(schemas.Model):
        foo = schemas.String()

    assert isinstance(SchemaA.fields.foo, schemas.BaseSchema)  # 类可访问

    # 实例不可访问
    with pytest.raises(AttributeError, match="""^'SchemaA' object has no attribute 'foo'$"""):
        assert SchemaA().foo


def test_get_model_field():
    class SchemaA(schemas.Model):
        _name = schemas.String()
        name = schemas.String()

    assert SchemaA.fields._name
    assert SchemaA().fields._name
    assert SchemaA.fields.name
    assert SchemaA().fields.name


def test_field_conflict():
    """Schema 字段和方法字段冲突

    目前不清楚怎么处理合适
    """

    class SchemaA(schemas.Model):
        deserialize = schemas.Integer()  # 和内置方法重名
        Meta = schemas.Integer()  # 和内置属性重名

    assert SchemaA.deserialize == schemas.Model.deserialize
    assert isinstance(SchemaA.fields.Meta, schemas.BaseSchema)
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

    with pytest.raises(ValidationError):
        try:
            Schema1().deserialize({
                'a1': 'a',
                'b1': {
                    'a2': 'a',
                    'b2': ['1', 'a'],
                    'c2': [{'a3': 'a'}]
                }
            })
        except ValidationError as e:
            assert e.format_errors() == {
                'a1': ['不是一个整数'],
                'b1': {
                    'a2': ['不是一个整数'],
                    'b2': {
                        1: ['不是一个整数']
                    },
                    'c2': {
                        0: {
                            'a3': ['不是一个整数']
                        }
                    }
                }
            }
            raise


def test_field_required():
    class SchemaA(schemas.Model):
        a = schemas.Integer(required=False)

    assert 'a' not in SchemaA().deserialize({})

    class SchemaB(schemas.Model):
        a = schemas.Integer(required=True)

    with pytest.raises(ValidationError):
        try:
            SchemaB().deserialize({})
        except ValidationError as e:
            assert e.format_errors() == {'a': ['这个字段是必需的']}
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
        a = schemas.String(validators=[validators.LengthValidator(min_length=6), validators.LengthValidator(
            max_length=2)])

    with pytest.raises(ValidationError):
        try:
            Schema1().deserialize({'a': '123'})
        except ValidationError as e:
            assert e.format_errors() == {'a': ['长度最小为 6', '长度最大为 2']}
            raise


def test_default_validators():
    def validate_time(data):
        if data['start_time'] > data['end_time']:
            raise ValidationError('开始时间不能大于结束时间')

    class Schema(schemas.Model):
        start_time = schemas.Datetime()
        end_time = schemas.Datetime()

        class Meta:
            default_validators = [validate_time]

    # error
    with pytest.raises(ValidationError, match='开始时间不能大于结束时间'):
        Schema().deserialize({'start_time': '2022-01-02', 'end_time': '2022-01-01'})

    # ok
    assert Schema().deserialize({'start_time': '2022-01-01', 'end_time': '2022-01-02'}) == {
        'start_time': datetime.datetime(2022, 1, 1),
        'end_time': datetime.datetime(2022, 1, 2),
    }


def test_serialize_empty_field():
    """Model 序列化时，字段返回 Empty，将不会序列化该字段"""

    class Schema(schemas.Model):
        a = schemas.Integer()
        b = schemas.String(fallback=lambda _: schemas.EMPTY)

    assert Schema().serialize({'a': 1}) == {'a': 1}
