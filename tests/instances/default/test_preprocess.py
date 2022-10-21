"""预处理/后处理"""
import json

import pytest
from django.db import models
from django_openapi import Operation, model2schema
from django_openapi.parameters import Body
from django_openapi.schema import schemas
from django_openapi.urls import reverse
from tests.utils import TestResource, ResourceView


class Schema(schemas.Model):
    array = schemas.List(serialize_preprocess=json.loads)
    object = schemas.Dict(serialize_preprocess=json.loads)

    class Meta:
        register_as_component = False


@TestResource
class Res(ResourceView):
    @Operation(
        summary='JSON string',
        response_schema=Schema,
    )
    def get(self):
        return dict(
            array=json.dumps(['a', 0, True, None]),
            object=json.dumps({'a': 1})
        )


def test_json_string(client):
    assert client.get(reverse(Res)).json() == {
        'array': ['a', 0, True, None],
        'object': {'a': 1},
    }


# 用 models.StringField 代替 models.JSONField 的场景


class JsonModel(models.Model):
    # array = models.JSONField()
    # object = models.JSONField()
    array = models.CharField(max_length=5000)
    object = models.CharField(max_length=5000)


@TestResource
class LikeJSONAPI:
    class LikeJsonSchema(model2schema(JsonModel)):
        array = schemas.List(serialize_preprocess=json.loads, deserialize_postprocess=json.dumps)
        object = schemas.Dict(serialize_preprocess=json.loads, deserialize_postprocess=json.dumps)

    @Operation(
        response_schema=LikeJsonSchema,
    )
    def post(self, body=Body(LikeJsonSchema)):
        JsonModel.objects.create(**body)
        instance = JsonModel.objects.first()
        return instance


@pytest.mark.django_db
def test_like_json_api(client):
    resp = client.post(reverse(LikeJSONAPI), data={
        'array': ['a', 0, True, None],
        'object': {'a': 1},
    }, content_type='application/json')
    assert resp.status_code == 200
    assert resp.json() == {'id': 1, 'array': ['a', 0, True, None], 'object': {'a': 1}}
