from django_openapi import Resource


@Resource("/items/{item_id}")
class API:
    def __init__(self, request, item_id):
        self.item_id = item_id

    def get(self):
        ...
