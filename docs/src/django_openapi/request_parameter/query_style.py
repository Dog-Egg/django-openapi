from django_openapi import Resource, schema
from django_openapi.parameter import Query, Style


class Color(schema.Model):
    R = schema.Integer()
    G = schema.Integer()
    B = schema.Integer()


@Resource("/to/path")
class API:
    def get(
        self,
        query=Query(
            {"color": Color()},
            {"color": Style("deepObject", True)},
        ),
    ):
        ...
