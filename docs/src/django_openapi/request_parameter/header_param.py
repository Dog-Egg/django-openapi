from django_openapi import Resource, schema
from django_openapi.parameter import Header


# 定义参数结构
class HeaderSchema(schema.Model):
    version = schema.String()


@Resource("/to/path")
class API:
    def get(self, header=Header(HeaderSchema)):
        ...
