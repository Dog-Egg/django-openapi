from django_openapi import Resource
from django_openapi.parameters import Query
from django_openapi.schema import schemas


@Resource('/path')
class API:
    # 默认值设为 1
    # highlight-next-line
    def get(self, query=Query({'a': schemas.Integer(default=1)})):
        # 在不传递参数的情况下，query = {'a': 1}
        return query
