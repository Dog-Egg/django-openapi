from django_openapi import Resource
# highlight-next-line
from django_openapi.parameters import Query
from django_openapi.schema import schemas


@Resource('/foo')
class API:
    # highlight-start
    def get(self, query=Query({
        'a': schemas.Integer(description='参数A'),
        'b': schemas.List(schemas.Integer(), description='参数B', required=False),
    })):
        # highlight-end
        pass
