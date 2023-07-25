from django_openapi import Resource, schema
from django_openapi.parameter import Cookie


# 定义参数结构
class CookieSchema(schema.Model):
    language = schema.String()


@Resource("/to/path")
class API:
    def get(self, cookie=Cookie(CookieSchema)):
        ...
