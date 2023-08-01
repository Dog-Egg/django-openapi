from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/path/to")
class API:
    def post(
        self,
        body=Body(
            {
                "gte": schema.Integer(minimum=0),
                "gt": schema.Integer(minimum=0, exclusive_minimum=True),
                "lte": schema.Integer(maximux=0),
                "lt": schema.Integer(maximux=0, exclusive_maximum=True),
                "price": schema.Float(minimum=0, multiple_of=0.01),
            }
        ),
    ):
        ...
