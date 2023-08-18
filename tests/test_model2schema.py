from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models

from django_openapi import model2schema, schema
from django_openapi.model2schema import parse


class A(models.Model):
    CharField = models.CharField(max_length=12)
    IntegerField = models.IntegerField()
    SmallIntegerField = models.SmallIntegerField()
    DecimalField = models.DecimalField(decimal_places=2, max_digits=5)
    JSONField = models.JSONField()
    FileField = models.FileField()


def test_A():
    result = parse(A)

    assert result["id"] == (
        schema.Integer,
        {"description": "ID", "read_only": True, "required": False},
    )
    assert result["CharField"] == (schema.String, {"max_length": 12})
    assert result["IntegerField"] == (schema.Integer, {})
    assert result["SmallIntegerField"] == (schema.Integer, {})
    assert result["JSONField"] == (schema.Any, {})
    assert result["FileField"] == (schema.File, {})


class B(models.Model):
    a1 = models.ForeignKey(A, on_delete=models.CASCADE)
    a2 = models.ForeignKey(A, on_delete=models.CASCADE, null=True, verbose_name="A")
    a3 = models.ForeignKey(A, on_delete=models.CASCADE, null=True, default=None)


def test_B():
    assert parse(B) == {
        "id": (
            schema.Integer,
            {"description": "ID", "read_only": True, "required": False},
        ),
        "a1_id": (
            schema.Integer,
            {},
        ),
        "a2_id": (schema.Integer, {"nullable": True, "description": "A"}),
        "a3_id": (schema.Integer, {"nullable": True, "default": None}),
    }


def test_FileField():
    class File(models.Model):
        file = models.FileField()

    FieldSchema = model2schema(File, include_fields=["file"])
    inst = File(file=SimpleUploadedFile("123.txt", b"hello"))
    assert FieldSchema().serialize(inst) == {"file": "/123.txt"}


def test_include_exclude_fields():
    """测试 include_fields 中的未知字段。"""

    class FooModel(models.Model):
        a = models.CharField()

    with pytest.raises(ValueError, match="Unknown include_fields: {'b'}."):
        model2schema(FooModel, include_fields=["b"])

    with pytest.raises(ValueError, match="Unknown exclude_fields: {'b'}."):
        model2schema(FooModel, exclude_fields=["b"])


def test_DecimalField():
    class FooModel2(models.Model):
        a = models.DecimalField(max_digits=5)

    FooSchema = model2schema(FooModel2)

    # deserialize
    assert FooSchema().deserialize({"a": 123.12}) == {"a": Decimal("123.12")}

    # deserialize error
    with pytest.raises(schema.ValidationError):
        try:
            FooSchema().deserialize({"a": 123.122})
        except schema.ValidationError as e:
            assert e.format_errors() == [
                {
                    "msgs": ["Ensure that there are no more than 5 digits in total."],
                    "loc": ["a"],
                }
            ]
            raise

    # serialize
    a = FooSchema().serialize({"a": Decimal("1"), "id": 1})["a"]
    assert a == 1 and isinstance(a, int)
    a = FooSchema().serialize({"a": Decimal("1.1"), "id": 1})["a"]
    assert a == 1.1 and isinstance(a, float)
