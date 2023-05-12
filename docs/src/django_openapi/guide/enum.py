from django_openapi import Resource, schema
from django_openapi.parameter import Query


@Resource("/to/path")
class API:
    def get(
        self,
        query=Query(
            {
                "fruit": schema.String(
                    choices=[
                        "apple",
                        "grape",
                        "watermelon",
                    ]
                )
            }
        ),
    ):
        ...
