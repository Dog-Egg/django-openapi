import types
import typing

from django.http.response import HttpResponseBase, HttpResponse, JsonResponse

from django_openapi import typing as _t, exceptions

__all__ = ['ResponseMaker']


class BaseResponseMaker:
    def make_response(self, rv, status_code: int) -> HttpResponseBase:
        raise NotImplementedError

    def handle_error(self, e: Exception):
        raise NotImplementedError


def http_error(status):
    def handler(_, e: Exception) -> HttpResponseBase:
        content = e.args[0] if e.args else b''
        return HttpResponse(content, status=status)

    return handler


def request_args_error(_, e: exceptions.RequestArgsError):
    return JsonResponse({'errors': e.errors}, status=400)


class ResponseMaker(BaseResponseMaker):
    __error_handlers: '_t.ErrorHandlers' = {
        exceptions.BadRequest: http_error(400),
        exceptions.Unauthorized: http_error(401),
        exceptions.Forbidden: http_error(403),
        exceptions.NotFound: http_error(404),
        exceptions.MethodNotAllowed: http_error(405),
        exceptions.UnsupportedMediaType: http_error(415),
        exceptions.RequestArgsError: request_args_error,  # type: ignore
    }

    class __ErrorHandler:
        def __init__(self, exc: typing.Type[Exception]):
            self.exc = exc

        def __call__(self, method):
            self.method = method
            return self

    errorhandler = __ErrorHandler

    def __init_subclass__(cls, **kwargs):
        error_handlers = cls.__error_handlers.copy()
        for val in vars(cls).values():
            if isinstance(val, cls.__ErrorHandler):
                error_handlers[val.exc] = val.method
        cls.__error_handlers = error_handlers

    def __init__(self, request):
        self.request = request

    def make_response(self, rv, status_code: int) -> HttpResponseBase:
        if isinstance(rv, HttpResponseBase):
            return rv

        if rv is None:
            rv = b''
        if isinstance(rv, (str, bytes)):
            return HttpResponse(rv, status=status_code)

        return JsonResponse(rv, status=status_code)

    def handle_error(self, e: Exception) -> HttpResponseBase:
        for cls in e.__class__.__mro__:
            if cls in self.__error_handlers and issubclass(cls, Exception):
                handler = self.__error_handlers[cls]
                handler = types.MethodType(handler, self)
                return handler(e)
        raise e
