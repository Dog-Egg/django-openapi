from django_openapi import Resource, schema
from django_openapi.parameter import Query


class QuerySchema(schema.Model):
    a = schema.String()
    b = schema.String(required=False)


@Resource("/to/path")
class API:
    def get(self, query=Query(QuerySchema)):
        ...
