from django_openapi import Resource


@Resource("/to/path")
class API:
    def head(self):
        ...

    def options(self):
        ...

    def get(self):
        ...

    def post(self):
        ...

    def put(self):
        ...

    def patch(self):
        ...

    def delete(self):
        ...

    def trace(self):
        ...
