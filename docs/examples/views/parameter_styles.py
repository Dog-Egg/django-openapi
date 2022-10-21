from django_openapi import Resource
from django_openapi.parameters import Query, Style
from django_openapi.schema import schemas


@Resource('/path')
class API:
    def get(self, query=Query({
        'a': schemas.List(),
        'b': schemas.List(style=Style(Style.PIPE_DELIMITED))
    })):
        pass
