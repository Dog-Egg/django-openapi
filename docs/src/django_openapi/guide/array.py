from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/to/path")
class API:
    def post(
        self,
        data=Body(
            {
                "maxItems": schema.List(schema.Integer, max_items=5),
                "minItems": schema.List(schema.Integer, min_items=3),
                "uniqueItems": schema.List(schema.Integer, unique_items=True),
            }
        ),
    ):
        ...
