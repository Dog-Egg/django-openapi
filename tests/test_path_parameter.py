import pytest

from django_openapi import OpenAPI, Resource
from django_openapi.schema import schemas


class ResourceClass:
    def __init__(self, request, arg):
        self.arg = arg

    def get(self):
        return {'arg': self.arg}


openapi = OpenAPI()
openapi.add_resource(Resource('/path/{arg}')(ResourceClass))
openapi.add_resource(Resource('/path2/{arg}', path_parameters={'arg': schemas.Integer()})(ResourceClass))
openapi.add_resource(Resource('/path3/{arg}', path_parameters={'arg': schemas.Path()})(ResourceClass))
openapi.add_resource(Resource('/path4{arg}', path_parameters={'arg': schemas.Path()})(ResourceClass))

urlpatterns = openapi.urls


@pytest.mark.urls('tests.test_path_parameter')
def test_default_parameter(client):
    response = client.get('/path/1')
    assert response.status_code == 200
    assert response.json() == {'arg': '1'}


@pytest.mark.urls('tests.test_path_parameter')
def test_schema_parameter(client):
    response = client.get('/path2/1')
    assert response.json() == {'arg': 1}


@pytest.mark.urls('tests.test_path_parameter')
def test_404(client):
    # openapi 的 404 响应
    response = client.get('/path2/asd')
    assert response.status_code == 404
    assert response.content == b''

    # django 的 404 响应
    response = client.get('/path2/asd/1')
    assert response.status_code == 404
    assert response.content != b''


@pytest.mark.urls('tests.test_path_parameter')
def test_path_schema(client):
    response = client.get('/path3/asd/123')
    assert response.json() == {'arg': 'asd/123'}

    response = client.get('/path4/asd/123')
    assert response.json() == {'arg': '/asd/123'}
