from django_openapi import Resource, schema
from django_openapi.parameter import Body, Query


@Resource("/to/path")
class API:
    def post(
        self,
        Body=Body(
            {
                "email": schema.String(
                    pattern=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
                ),
            }
        ),
    ):
        ...
