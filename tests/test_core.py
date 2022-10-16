from django_openapi.core import OpenAPI
from django_openapi.urls import reverse
from tests.utils import TestResource


def test_openapi_id():
    openapi1, openapi2 = OpenAPI(), OpenAPI()
    openapi3 = OpenAPI()
    assert openapi1.id == openapi2.id
    assert openapi1.id != openapi3.id


@TestResource
class API:
    def get(self):
        pass


def test_class_without_init_method(client):
    """
    测试被Resource装饰的类可以不需要定义 def __init__
    """
    resp = client.get(reverse(API))
    assert resp.status_code == 200
