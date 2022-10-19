from django_openapi import Operation
from django_openapi.parameters import Body
from django_openapi.schema import schemas
from django_openapi.urls import reverse
from tests.utils import TestResource, itemgetter


class NullableSchema(schemas.Model):
    a = schemas.String()


@TestResource
class API:
    @Operation(response_schema=dict(data=NullableSchema(nullable=True)))
    def post(self, query=Body(dict(data=NullableSchema(nullable=True)))):
        return query


def test_with_request(client):
    resp = client.post(reverse(API), data=dict(data=None), content_type='application/json')
    assert resp.json() == {'data': None}


def test_oas1(oas):
    assert itemgetter(oas, ['paths', reverse(API), 'post', 'requestBody', 'content', 'application/json', 'schema',
                            'properties', 'data', 'allOf']) == [
               {
                   "$ref": "#/components/schemas/09c8b2a5.NullableSchema"
               },
               {
                   "nullable": True
               }
           ]


def test_oas2(oas):
    assert itemgetter(oas, ['paths', reverse(API), 'post', 'responses', '200', 'content', 'application/json', 'schema',
                            'properties', 'data', 'allOf']) == [
               {
                   "$ref": "#/components/schemas/09c8b2a5.NullableSchema"
               },
               {
                   "nullable": True
               }
           ]


def test_oas3(oas):
    assert 'nullable' not in itemgetter(oas, ['components', 'schemas', '09c8b2a5.NullableSchema'])
