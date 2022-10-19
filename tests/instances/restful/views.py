from django.db import models
from django.contrib.auth.models import User

from django_openapi import Resource, Operation, model2schema
from django_openapi.exceptions import NotFound
from django_openapi.pagination import PageNumberPaginator
from django_openapi.parameters import Body


class UserSchema(model2schema(
    User,
    extra_kwargs=dict(
        username=dict(max_length=20),
        password=dict(max_length=16, write_only=True)
    )
)):
    class Meta:
        schema_name = '用户对象'


@Resource('/users')
class UsersResource:
    def __init__(self, request):
        pass

    @Operation(summary='获取用户列表')
    def get(self, paginator=PageNumberPaginator(UserSchema)):
        return paginator.paginate(User.objects.all())

    @Operation(
        summary='创建用户',
        response_schema=UserSchema,
        status_code=201,
    )
    def post(self, body=Body(UserSchema.partial(include_fields=['username', 'password']))):
        return User.objects.create_user(**body)


@Resource('/users/{uid}', path_parameters=dict(uid=UserSchema.fields.id))
class UserResource:
    def __init__(self, request, uid):
        try:
            self.user = User.objects.get(pk=uid)
        except models.ObjectDoesNotExist:
            raise NotFound

    @Operation(
        summary='获取用户',
        response_schema=UserSchema,
    )
    def get(self):
        return self.user

    @Operation(
        summary='更新用户',
        response_schema=UserSchema,
    )
    def put(self, body=Body(UserSchema(required_fields='__all__'))):
        for k, v in body.items():
            setattr(self.user, k, v)
        else:
            self.user.save()
        return self.user

    @Operation(
        summary='更新用户',
        response_schema=UserSchema,
    )
    def patch(self, body=Body(UserSchema(required_fields=[]))):
        return self.put(body=body)

    @Operation(
        summary='删除用户',
        status_code=204,
    )
    def delete(self):
        self.user.delete()
