import datetime
from unittest import mock

import pytest

from django_openapi.spec import utils as _spec
from django_openapi.schema import schemas
from django_openapi.schema.exceptions import ValidationError
from django_openapi.schema.schemas import BaseSchema
from django_openapi.schema.validators import RangeValidator


def test_number_range():
    assert schemas.Integer(gte=1).deserialize('1') == 1

    with pytest.raises(ValidationError, match='^The value must be greater than 1$'):
        schemas.Integer(gt=1).deserialize(1)

    with pytest.raises(ValidationError,
                       match="['The value must be less than 1', 'The value must be greater than 1']"):
        schemas.Integer(gt=1, validators=[RangeValidator(lt=1)]).deserialize(1)


def test_number_multiple():
    assert schemas.Integer(multiple_of=3).deserialize('9') == 9

    with pytest.raises(ValidationError, match='^The value must be a multiple of 4$'):
        schemas.Integer(multiple_of=4).deserialize(9)

    # multiple_of=0.01 可用于如"价格"的表示
    assert schemas.Float(multiple_of=0.01, gte=0).deserialize(1.01) == 1.01
    assert schemas.Float(multiple_of=0.01).deserialize(1) == 1

    with pytest.raises(ValidationError, match='^The value must be a multiple of 0.01$'):
        schemas.Float(multiple_of=0.01).deserialize(1.002)


def test_field_blank():
    # 不可为空
    class Schema1(schemas.Model):
        f1 = schemas.String()
        f2 = schemas.Integer(required=False)

    try:
        Schema1().deserialize({'f1': '', 'f2': ''})
    except ValidationError as exc:
        assert exc.format_errors() == {'f1': ['字段不能为空']}

    # 可为空
    class Schema2(schemas.Model):
        f1 = schemas.String(allow_blank=True)

    assert Schema2().deserialize({'f1': ' '}) == {'f1': ' '}

    # 可为空但是类型错误
    class Schema3(schemas.Model):
        f1 = schemas.Integer(allow_blank=True)

    try:
        Schema3().deserialize({'f1': ''})
    except ValidationError as exc:
        assert exc.format_errors() == {'f1': ['不是一个整数']}

    # 实际应用
    class Search(schemas.Model):
        arg1 = schemas.Integer(required=False)
        arg2 = schemas.Integer(required=False)

    assert Search().deserialize({'arg1': '', 'arg2': '123'}) == {'arg2': 123}


def test_any_nullable():
    assert schemas.String().nullable is False
    assert schemas.Any().nullable is True  # Any nullable 默认为 True


def test_fallback_1():
    """测试一种 fallback 输出的情景"""

    class Response(schemas.Model):
        code = schemas.Integer(fallback=lambda _: 200)

        data = schemas.Any(fallback=lambda _: None, nullable=False)

    assert Response().serialize({}) == {'code': 200, 'data': None}


def test_fallback_call_times():
    """fallback 在一次序列时调用次数"""

    def fallback1(value):
        m(value)  # 1次
        return datetime.date(2022, 1, 1)

    def fallback2(value):
        m(value)  # 2次
        return '2022-01-01'

    def _test_(fallback):
        class Schema(schemas.Model):
            date = schemas.Date(fallback=fallback)

        assert Schema().serialize({}) == {'date': '2022-01-01'}

    m = mock.Mock()
    _test_(fallback2)
    m.assert_has_calls([mock.call(schemas.EMPTY), mock.call('2022-01-01')])

    m = mock.Mock()
    _test_(fallback1)
    m.assert_has_calls([mock.call(schemas.EMPTY)])


def test_list_validators():
    class Schema(schemas.Model):
        items = schemas.List(unique_items=True, min_items=4)

    try:
        Schema().deserialize({'items': [{}, {}]})
    except ValidationError as e:
        assert e.format_errors() == {'items': ['长度最小为 4', 'The item is not unique']}


def test_schema_meta():
    assert not hasattr(schemas.BaseSchema, '_metadata')

    class MySchema(BaseSchema):
        pass

    assert _spec.clean(MySchema().to_spec()) == {'type': 'string'}
    assert MySchema._metadata['register_as_component'] is True

    class MySchema1(MySchema):
        class Meta:
            data_type = 'integer'
            register_as_component = False

    assert _spec.clean(MySchema1().to_spec()) == {'type': 'integer'}
    assert MySchema1._metadata['register_as_component'] is False

    class MySchema2(MySchema1):
        class Meta:
            data_format = 'x-format'

    assert _spec.clean(MySchema2().to_spec()) == {'type': 'integer', 'format': 'x-format'}
    assert MySchema2._metadata['register_as_component'] is True
