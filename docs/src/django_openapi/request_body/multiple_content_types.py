from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/login")
class API:
    def post(
        self,
        body=Body(
            {
                "username": schema.String(),
                "password": schema.Password(),
            },
            content_type=[
                "multipart/form-data",
                "application/json",
            ],
        ),
    ):
        ...
