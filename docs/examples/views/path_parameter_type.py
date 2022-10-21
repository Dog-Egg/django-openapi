from django_openapi import Resource
from django_openapi.schema import schemas


# 使用 path_parameters 声明路径参数类型
# highlight-next-line
@Resource('/path/{id}', path_parameters={'id': schemas.Integer()})
class API2:
    def __init__(self, request, id):
        pass

    def post(self):
        pass
