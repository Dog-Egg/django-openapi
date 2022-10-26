from django_openapi.parameters import Body
from django_openapi.schema import schemas
from django_openapi.urls import reverse
from tests.utils import TestResource


class Schema(schemas.Model):
    a = schemas.Integer()


@TestResource
class API:
    @staticmethod
    def post(body=Body(dict(
        a=schemas.Dict(),
        b=schemas.Dict(Schema),
        c=schemas.Dict(schemas.Integer, required=False),
    ))):
        return body


def test(client):
    resp = client.post(reverse(API), data=dict(a={'foo': 'a'}, b={'a': {'a': '1'}}), content_type='application/json')
    assert resp.json() == {'a': {'foo': 'a'}, 'b': {'a': {'a': 1}}}
