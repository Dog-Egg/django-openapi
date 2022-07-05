from django.contrib.auth import login, authenticate, logout

from openapi.core import API, Operation
from openapi.http.exceptions import BadRequest
from openapi.parameters import Body
from openapi.schemax import fields


class Auth(API):
    @Operation(
        summary='登录',
    )
    def post(self, request, body=Body(dict(
        username=fields.String(),
        password=fields.String(),
    ))):
        user = authenticate(request, **body)
        if user:
            login(request, user)
        else:
            raise BadRequest({'message': '用户名或密码错误'})

    @Operation(
        summary='登出'
    )
    def delete(self, request):
        logout(request)
