from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/to/path")
class API:
    def get(
        self,
        body=Body(
            dict(
                a=schema.String(description="不可为空（默认）"),
                b=schema.String(
                    nullable=True,
                    description="可为空",
                ),
            )
        ),
    ):
        ...
