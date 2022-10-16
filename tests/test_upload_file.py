"""文件上传"""
import django
import pytest

from django.db import models
from django.core.files.uploadedfile import SimpleUploadedFile

from django_openapi import model2schema, Operation
from django_openapi.parameters import Body
from django_openapi.schema import schemas
from django_openapi.urls import reverse
from tests.utils import TestResource, ResourceView, itemgetter


class UploadedFile(models.Model):
    file = models.FileField(upload_to='tmp')


class UploadedFileSchema(model2schema(UploadedFile)):
    pass


@TestResource
class Res(ResourceView):
    @staticmethod
    @Operation(
        response_schema=UploadedFileSchema,
        description='上传文件需要设置 content-type 为 multipart/form-data'
    )
    def post(body=Body(dict(file=schemas.File()), content_type='multipart/form-data')):
        instance = UploadedFile(file=body['file'])
        instance.save()
        return instance


@pytest.mark.django_db
def test_upload_file(client):
    resp = client.post(
        reverse(Res),
        dict(file=SimpleUploadedFile("test.mp4", b"", content_type="video/mp4"))
    )
    assert resp.status_code == 200
    data = resp.json()
    assert 'id' in data and 'file' in data

    if django.VERSION <= (3, 0):
        assert data['file'].startswith('/')


def test_oas(get_oas):
    # FileSchema 只能是只读
    assert itemgetter(get_oas(),
                      ['components', 'schemas', '30689379.UploadedFileSchema', 'properties', 'file',
                       'readOnly']) is True
