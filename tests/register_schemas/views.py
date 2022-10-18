from django_openapi.parameters import Body
from .schemas import SchemaA
from tests.utils import TestResource


@TestResource
class API:
    def post(self, body=Body(SchemaA)):
        pass
