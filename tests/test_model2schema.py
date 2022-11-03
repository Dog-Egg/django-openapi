"""model2schema"""
import datetime
import re
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import models

from django_openapi.model2schema import model2schema
from django_openapi.schema import schemas
from django_openapi.schema.exceptions import ValidationError
from django_openapi.pagination import PageNumberPaginator
from tests.utils import TestResource, ResourceView


def test_to_schema():
    class Foo(models.Model):
        pass

    schema_cls = model2schema(Foo)
    assert issubclass(schema_cls, schemas.Model)
    assert schema_cls.fields.__len__() == 1
    assert isinstance(schema_cls.fields.id, schemas.Integer)
    assert schema_cls.fields.id.read_only is True  # pk 不可写


def test_char_field():
    class Char(models.Model):
        char = models.CharField(max_length=3)

    schema_cls = model2schema(Char)
    assert isinstance(schema_cls.fields.char, schemas.String)
    assert schema_cls.fields.char.max_length == 3

    with pytest.raises(ValidationError,
                       match=re.escape(
                           """{'char': ['长度最大为 3']}""")):
        schema_cls().deserialize({'char': '1234'})


def test_decimal_field():
    class Goods(models.Model):
        price = models.DecimalField(max_digits=5, decimal_places=2)

    assert Goods._meta.get_field('price').to_python(1.99) == Decimal('1.99')

    schema_cls = model2schema(Goods)
    assert isinstance(schema_cls.fields.price, schemas.Float)
    assert schema_cls.fields.price.lt == 1000
    assert schema_cls.fields.price.multiple_of == 0.01


def test_null():
    class FooNull(models.Model):
        f1 = models.IntegerField()
        f2 = models.IntegerField(null=True)

    schema_cls = model2schema(FooNull)
    assert schema_cls.fields.f1.nullable is False
    assert schema_cls.fields.f2.nullable is True


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
    assert schema_cls.fields.d1.read_only is False
    assert schema_cls.fields.d2.read_only is True
    assert schema_cls().deserialize({'d1': '2021-03-05'}) == {'d1': datetime.datetime(2021, 3, 5)}


@TestResource
class Res(ResourceView):
    class User(model2schema(User, extra_kwargs=dict(password=dict(write_only=True)))):
        """用户对象"""
        pass

    @staticmethod
    def get(paginator=PageNumberPaginator(User)):
        return paginator.paginate(User.objects.all())


class PermissionTree(models.Model):
    code = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True)
    parent = models.ForeignKey('PermissionTree', on_delete=models.CASCADE, null=True, verbose_name='父节点ID')


@pytest.mark.django_db
def test_foreignkey():
    schema = model2schema(PermissionTree)
    assert isinstance(schema.fields.parent_id, schemas.Integer)
    assert schema.fields.parent_id.alias == 'parent_id'
    assert schema.fields.parent_id.description == "父节点ID"
    assert schema.fields.parent_id.nullable is True
    assert schema.fields.parent_id.required is True

    instance1 = PermissionTree.objects.create(code='code')
    data = schema(unknown_fields='error').deserialize(dict(code='code', parent_id=1))
    instance2 = PermissionTree.objects.create(**data)
    assert instance2.parent == instance1

    assert schema().serialize(instance2) == {'code': 'code', 'description': '', 'id': 2, 'parent_id': 1}
