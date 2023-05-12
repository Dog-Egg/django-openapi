from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import models

from django_openapi import model2schema


def test_FileField():
    class File(models.Model):
        file = models.FileField()

    FieldSchema = model2schema(File, include_fields=["file"])
    inst = File(file=SimpleUploadedFile("123.txt", b"hello"))
    assert FieldSchema().serialize(inst) == {"file": "/123.txt"}
