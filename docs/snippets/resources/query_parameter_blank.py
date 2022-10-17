from django_openapi import Resource
from django_openapi.parameters.parameters import Query
from django_openapi.schema import schemas


@Resource('/path')
class API:
    def get(self, query=Query({
        'a': schemas.String(required=False),
        # highlight-next-line
        'b': schemas.String(required=False, allow_blank=True),
    })):
        # 参数 ?a=&b= 将得到 query = {'b': ''}
        return query
