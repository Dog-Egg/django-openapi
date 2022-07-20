import datetime
import re
from decimal import Decimal

import pytest
from django.db import models

from openapi.extension.model2schema import model2schema
from openapi.schema import schemas
from openapi.schema.exceptions import DeserializationError


def test_to_schema():
    class Foo(models.Model):
        pass

    schema_cls = model2schema(Foo)
    assert issubclass(schema_cls, schemas.Model)
    assert schema_cls.__name__ == 'Foo'
    assert schema_cls._fields.__len__() == 1
    assert isinstance(schema_cls.id, schemas.Integer)
    assert schema_cls.id.serialize_only is True  # pk 不可写


def test_char_field():
    class Char(models.Model):
        char = models.CharField(max_length=3)

    schema_cls = model2schema(Char)
    assert isinstance(schema_cls.char, schemas.String)
    assert schema_cls.char.max_length == 3

    with pytest.raises(DeserializationError,
                       match=re.escape(
                           """{'char': ['长度最大为 3']}""")):
        schema_cls().deserialize({'char': '1234'})


def test_decimal_field():
    class Goods(models.Model):
        price = models.DecimalField(max_digits=5, decimal_places=2)

    assert Goods._meta.get_field('price').to_python(1.99) == Decimal('1.99')

    schema_cls = model2schema(Goods)
    assert isinstance(schema_cls.price, schemas.Float)
    assert schema_cls.price.lt == 1000
    assert schema_cls.price.multiple_of == 0.01


def test_null():
    class FooNull(models.Model):
        f1 = models.IntegerField()
        f2 = models.IntegerField(null=True)

    schema_cls = model2schema(FooNull)
    assert schema_cls.f1.nullable is False
    assert schema_cls.f2.nullable is True


def test_bool_field():
    class BooleanModel(models.Model):
        b1 = models.BooleanField()
        b2 = models.NullBooleanField()

    schema_cls = model2schema(BooleanModel)
    assert schema_cls().deserialize({'b1': '1', 'b2': None}) == {'b1': True, 'b2': None}


def test_datetime_field():
    class DatetimeModel(models.Model):
        d1 = models.DateTimeField()
        d2 = models.DateTimeField(auto_now_add=True)

    schema_cls = model2schema(DatetimeModel)
    assert schema_cls.d1.serialize_only is False
    assert schema_cls.d2.serialize_only is True
    assert schema_cls().deserialize({'d1': '2021-03-05'}) == {'d1': datetime.datetime(2021, 3, 5)}
