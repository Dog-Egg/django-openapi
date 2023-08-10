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
    assert parse(A) == {
        "id": (
            schema.Integer,
            {"description": "ID", "read_only": True, "required": False},
        ),
        "CharField": (schema.String, {"max_length": 12}),
        "IntegerField": (schema.Integer, {}),
        "SmallIntegerField": (schema.Integer, {}),
        "DecimalField": (
            schema.Float,
            {"exclusive_maximum": True, "maximum": 1000, "multiple_of": 0.01},
        ),
        "JSONField": (schema.Any, {}),
        "FileField": (schema.File, {}),
    }


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
