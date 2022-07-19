from django.contrib.auth import login, authenticate, logout
from django.http import JsonResponse

from openapi.core import API, Operation
from openapi.http.exceptions import abort
from openapi.parameters import Body
from openapi.schema import schemas


class Auth(API):
    @Operation(
        summary='登录',
    )
    def post(self, request, body=Body(dict(
        username=schemas.String(description='用户名'),
        password=schemas.Password(description='密码'),
    ), content_type=['application/x-www-form-urlencoded', 'application/json'])):
        user = authenticate(request, **body)
        if user:
            login(request, user)
        else:
            abort(JsonResponse({'message': '用户名或密码错误'}))

    @Operation(
        summary='登出'
    )
    def delete(self, request):
        logout(request)
