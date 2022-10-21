from django.contrib.auth.models import User

from django_openapi import Resource, Operation, model2schema
from django_openapi.schema import schemas


@Resource('/path')
class API:
    @Operation(
        # response_schema 用于提供接口响应描述，可以是一个字典
        # highlight-start
        response_schema={
            'name': schemas.String(description='姓名'),
            'age': schemas.Integer(description='年龄', lte=0),
        }
        # highlight-end
    )
    def get(self):
        return {'name': '张三', 'age': 30}


@Resource('/users/{uid}')
class API2:
    def __init__(self, request, uid):
        self.uid = uid

    class UserSchema(model2schema(User)):
        pass

    @Operation(
        summary='获取用户信息',
        # response_schema 也可以是一个 Schema
        # highlight-next-line
        response_schema=UserSchema
    )
    def get(self):
        # 由于定义了 response_schema，response_schema 会将返回值序列化
        # 所以这里可以直接返回了一个 User 对象，而无需手动序列化
        # highlight-next-line
        return User.objects.get(self.uid)
