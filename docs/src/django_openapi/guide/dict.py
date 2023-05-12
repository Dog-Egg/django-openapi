from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/to/path")
class API:
    def post(
        self,
        data=Body(
            {
                "dict": schema.Dict(),
                "dictInt": schema.Dict(schema.Integer),
                "maxProperties": schema.Dict(max_properties=2),
                "minProperties": schema.Dict(min_properties=2),
            }
        ),
    ):
        ...
