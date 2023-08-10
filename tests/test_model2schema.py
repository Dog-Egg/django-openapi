import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models

from django_openapi import model2schema
from django_openapi.model2schema import match_convertor


def extract_arguments(field: models.Field):
    convertor = match_convertor(type(field))
    assert convertor
    return convertor.extract_arguments(field)


def test_FileField():
    class File(models.Model):
        file = models.FileField()

    FieldSchema = model2schema(File, include_fields=["file"])
    inst = File(file=SimpleUploadedFile("123.txt", b"hello"))
    assert FieldSchema().serialize(inst) == {"file": "/123.txt"}


def test_DecimalField():
    kwargs = extract_arguments(models.DecimalField(decimal_places=2, max_digits=6))
    assert kwargs == {
        "maximum": 10000,
        "exclusive_maximum": True,
        "multiple_of": 0.01,
    }


def test_include_fields():
    """测试 include_fields 中的未知字段。"""

    class FooModel(models.Model):
        a = models.CharField()

    with pytest.raises(ValueError, match="Unknown include_fields: {'b'}"):
        model2schema(FooModel, include_fields=["b"])
