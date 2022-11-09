import pytest
from django.db import models, IntegrityError

from django_openapi import model2schema, Operation
from django_openapi.parameters import Body
from django_openapi.schema import schemas
from django_openapi.urls import reverse
from tests.utils import TestResource

try:
    from django.db.models import JSONField
except ImportError:
    JSONField = None
else:
    class JsonModel2(models.Model):
        json = models.JSONField()
        json2 = models.JSONField(null=True, blank=True, help_text='可以为空或不填')


    JsonModelSchema = model2schema(JsonModel2)


    class NewJsonModelSchema(JsonModelSchema):  # type: ignore
        """限制 json2 字段为对象"""

        class Object(schemas.Model):
            a = schemas.Integer()

            class Meta:
                register_as_component = False

        json2 = Object(**JsonModelSchema.fields.json2.kwargs)


    @TestResource
    class JSONAPI:
        @staticmethod
        @Operation(response_schema=JsonModelSchema)
        def post(body=Body(JsonModelSchema)):
            instance = JsonModel2(**body)
            instance.save()
            return JsonModel2.objects.get(pk=instance.pk)

        @Operation(
            response_schema=NewJsonModelSchema
        )
        def put(self, body=Body(NewJsonModelSchema)):
            instance = JsonModel2(**body)
            instance.save()
            return JsonModel2.objects.get(pk=instance.pk)

pytestmark = pytest.mark.skipif(JSONField is None, reason='No JSONField')


@pytest.mark.django_db
def test_jsonfield_null():
    """数据库NOT NULL JSON 是不能直接存储 NULL 的。"""
    with pytest.raises(IntegrityError):
        JsonModel2(json=None).save()


@pytest.mark.django_db
def test_jsonfield():
    assert JsonModelSchema.fields.json.required is True
    assert JsonModelSchema.fields.json.nullable is False
    assert JsonModelSchema.fields.json2.nullable is True
    assert JsonModelSchema.fields.json2.required is False

    JsonModel2(**JsonModelSchema().deserialize({'json': 1})).save()
    JsonModel2(**JsonModelSchema().deserialize({'json': 1, 'json2': None})).save()


@pytest.mark.django_db
def test_json_blank(client):
    response = client.post(reverse(JSONAPI), data={'json': 1}, content_type='application/json')
    assert response.json() == {'id': 1, 'json': 1, 'json2': None}


@pytest.mark.django_db
def test_put_request(client):
    response = client.put(reverse(JSONAPI), data={'json': '1', 'json2': {'a': 1}}, content_type='application/json')
    assert response.json() == {'id': 1, 'json': '1', 'json2': {'a': 1}}
