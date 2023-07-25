from django_openapi import Resource, schema
from django_openapi.parameter import Query


# 定义参数结构
class QuerySchema(schema.Model):
    a = schema.String()
    b = schema.Integer()


@Resource("/to/path")
class API:
    def get(self, query=Query(QuerySchema)):
        ...
