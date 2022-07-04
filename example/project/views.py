from django.contrib.auth import login, authenticate, logout

from openapi.core import API, Operation
from openapi.http.exceptions import BadRequest
from openapi.schemax import fields
from openapi.schemax.fields import Schema


class Auth(API):
    @Operation(
        summary='登录',
        body=Schema.from_dict(dict(
            username=fields.String(),
            password=fields.String(),
        ))
    )
    def post(self, request):
        body = request.data['body']
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

