from django.http import JsonResponse

from django_openapi import Respond
from django_openapi.exceptions import RequestArgsError, NotFound
from tests.utils import TestOpenAPI
from . import tests as views
from .exceptions import MyError


class MyRespond(Respond):
    def make_response(self, rv, status_code: int):
        if isinstance(rv, (dict, list)):
            return JsonResponse(dict(code=0, data=rv, message='ok'), status=status_code)
        return super().make_response(rv, status_code)

    @Respond.errorhandler(NotFound)
    def handle_not_found(self, _):
        return JsonResponse({'code': 404})

    @Respond.errorhandler(RequestArgsError)
    def handle_request_args_error(self, e: RequestArgsError):
        return JsonResponse({'code': 400, 'errors': e.errors}, status=422)

    @Respond.errorhandler(MyError)
    def handle_my_error(self, e):
        return JsonResponse(dict(code=1, message='error'), status=200)


openapi = TestOpenAPI(
    title='自定义 Response',
    respond=MyRespond,
    description="""
    通过 respond 可以修改响应风格，如：
    
    `{ "code": 0, "data": <response>, "message": "ok" }`
    
    `{ "code": 1, "message": "error"}`
    
    同时也能自定义异常处理
    """
)
openapi.find_resources(views)
