from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.urls import path, include
from django_openapi import Resource, model2schema, Operation, OpenAPI
from django_openapi.exceptions import NotFound
from django_openapi.pagination import PageNumberPaginator
from django_openapi.parameters import Body
from django_openapi.schema import schemas

UserSchema = model2schema(User)


@Resource('/users')
class UsersAPI:
    @Operation(summary='获取用户分页列表')
    def get(self, paginator=PageNumberPaginator(UserSchema)):
        return paginator.paginate(User.objects.all())

    @Operation(summary='新增用户', response_schema=UserSchema)
    def post(self, body=Body(UserSchema)):
        return User.objects.create(**body)


@Resource(
    '/users/{uid}',
    path_parameters={'uid': schemas.Integer()}
)
class UserAPI:
    def __init__(self, request, uid):
        try:
            self.user = User.objects.get(pk=uid)
        except ObjectDoesNotExist:
            raise NotFound

    @Operation(summary='获取用户', response_schema=UserSchema)
    def get(self):
        return self.user

    @Operation(summary='更新用户', response_schema=UserSchema)
    def put(self, body=Body(UserSchema(required_fields='__all__'))):
        return self.update_user(**body)

    @Operation(summary='更新用户', response_schema=UserSchema)
    def patch(self, body=Body(UserSchema(required_fields=[]))):
        return self.update_user(**body)

    @Operation(summary='删除用户')
    def delete(self):
        self.user.delete()

    def update_user(self, **kwargs):
        for name, val in kwargs.values():
            setattr(self.user, name, val)
        self.user.save()
        return self.user


openapi = OpenAPI()
openapi.add_resource(UsersAPI)
openapi.add_resource(UserAPI)

urlpatterns = [
    path('api/', include(openapi))
]
