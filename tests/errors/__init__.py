from django.http import JsonResponse, HttpResponse

from django_openapi.exceptions import RequestArgsError, NotFound
from tests.utils import TestOpenAPI
from . import tests as views
from .exceptions import MyError

openapi = TestOpenAPI(title='自定义响应错误')
openapi.find_resources(views)


@openapi.errorhandler(NotFound)
def handle_not_found(_):
    return JsonResponse({'errorCode': 404})


@openapi.errorhandler(RequestArgsError)
def handle_request_args_error(e: RequestArgsError):
    return JsonResponse({'err': e.errors}, status=422)


@openapi.errorhandler(MyError)
def handle_my_error(e):
    return HttpResponse('custom error', status=200)
