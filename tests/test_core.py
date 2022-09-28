from django_openapi.core import OpenAPI


def test_openapi_id():
    openapi1, openapi2 = OpenAPI(), OpenAPI()
    openapi3 = OpenAPI()
    assert openapi1.id == openapi2.id
    assert openapi1.id != openapi3.id
