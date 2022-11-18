"""OAS测试"""
from django_openapi.parameters import Body
from django_openapi.schema import schemas
from tests.utils import TestResource


@TestResource
class APIDescription:
    class SearchSchema(schemas.Model):
        class Info(schemas.Model):
            """信息"""

        info = Info()
        include = Info(description='包含')
        exclude = Info(description='不包含')

    def post(self, body=Body(SearchSchema)):
        pass
