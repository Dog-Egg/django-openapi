from django.http import JsonResponse
from django.http.response import HttpResponseBase, HttpResponse

from django_openapi import exceptions
from django_openapi import typing as _t


def http_error(status):
    def handler(e: Exception) -> HttpResponseBase:
        content = e.args[0] if e.args else b''
        return HttpResponse(content, status=status)

    return handler


def raise_response(e: exceptions.RaiseResponse):
    return e.response


def request_args_error(e: exceptions.RequestArgsError):
    return JsonResponse({'errors': e.errors}, status=400, safe=False)


default_error_handlers: _t.ErrorHandlers = {
    exceptions.BadRequest: http_error(400),
    exceptions.Unauthorized: http_error(401),
    exceptions.Forbidden: http_error(403),
    exceptions.NotFound: http_error(404),
    exceptions.MethodNotAllowed: http_error(405),
    exceptions.UnsupportedMediaType: http_error(415),

    exceptions.RaiseResponse: raise_response,  # type: ignore
    exceptions.RequestArgsError: request_args_error,  # type: ignore
}
