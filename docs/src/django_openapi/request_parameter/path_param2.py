from django_openapi import Resource, schema
from django_openapi.parameter import Path


@Resource(
    Path(
        "/items/{item_id}",
        {"item_id": schema.Integer()},
    )
)
class API:
    def __init__(self, request, item_id):
        self.item_id = item_id

    def get(self):
        ...
