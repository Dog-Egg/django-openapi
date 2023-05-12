from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/path/to")
class API:
    def post(
        self,
        body=Body(
            {
                "gt": schema.Integer(gt=0),
                "gte": schema.Integer(gte=0),
                "lt": schema.Integer(lt=0),
                "lte": schema.Integer(lte=0),
                "price": schema.Float(gte=0, multiple_of=0.01),
            }
        ),
    ):
        ...
