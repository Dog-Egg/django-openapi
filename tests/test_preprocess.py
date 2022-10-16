"""预处理"""
import json

from django_openapi import Operation
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
