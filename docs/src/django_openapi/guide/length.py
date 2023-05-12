from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/to/path")
class API:
    def post(
        self,
        data=Body(
            {
                "maxLength": schema.String(max_length=12),
                "minLength": schema.String(min_length=6),
                "length": schema.String(min_length=6, max_length=12),
            }
        ),
    ):
        ...
