from django.http import JsonResponse

from django_openapi import Respond
from django_openapi.exceptions import RequestArgsError, NotFound
from tests.utils import TestOpenAPI
from .exceptions import MyError


class MyRespond(Respond):
    def make_response(self, rv, status_code: int):
        if isinstance(rv, (dict, list)):
            return JsonResponse(dict(code=0, data=rv, message='ok'), status=status_code)
        return super().make_response(rv, status_code)

    def handle_error(self, e: Exception):
        if isinstance(e, NotFound):
            return JsonResponse({'code': 404})
        if isinstance(e, RequestArgsError):
            return JsonResponse({'code': 400, 'errors': e.errors}, status=422)
        if isinstance(e, MyError):
            return JsonResponse(dict(code=1, message='error'), status=200)
        return super().handle_error(e)


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
openapi.find_resources(__package__)
