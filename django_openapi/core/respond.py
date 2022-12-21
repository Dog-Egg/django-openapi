from django.http.response import HttpResponseBase, HttpResponse, JsonResponse

from django_openapi import exceptions

__all__ = ['Respond']


class BaseRespond:
    def make_response(self, rv, status_code: int) -> HttpResponseBase:
        raise NotImplementedError

    def handle_error(self, e: Exception):
        raise NotImplementedError


class Respond(BaseRespond):
    """
    处理请求方法函数的返回值或异常，并返回正确的 HTTP 响应。

    :param request: Django `Request` 对象。
    """

    def __init__(self, request):
        #: 接收的 Django `Request` 对象
        self.request = request

    def make_response(self, rv, status_code: int) -> HttpResponseBase:
        """
        处理请求函数返回值，需要返回 Django Response 实例，可继承自定义需要或用此提供一定代码约束。

        :param rv: 请求函数的返回值。
        :param status_code: 请求函数 `Operation` 定义的 `status_code` 参数，默认情况下为 200。
        :return: Django `Response` 对象。
        """
        if isinstance(rv, HttpResponseBase):
            return rv

        if rv is None:
            rv = b''
        if isinstance(rv, (str, bytes)):
            return HttpResponse(rv, status=status_code)

        return JsonResponse(rv, status=status_code)

    def handle_error(self, e: Exception) -> HttpResponseBase:
        """
        处理请求函数抛出的异常，可返回 Django Response 实例，也可继续抛出，可继承自定义需要或用此提供一定代码约束。

        :param e: 请求函数抛出的异常。
        :return: Django `Response` 对象。
        """

        def make_response(status_code):
            content = e.args[0] if e.args else b''
            return Respond.make_response(..., content, status_code)

        if isinstance(e, exceptions.RequestArgsError):
            return JsonResponse({'errors': e.errors}, status=400)

        if isinstance(e, exceptions.BadRequest):
            return make_response(400)
        if isinstance(e, exceptions.Unauthorized):
            return make_response(401)
        if isinstance(e, exceptions.Forbidden):
            return make_response(403)
        if isinstance(e, exceptions.NotFound):
            return make_response(404)
        if isinstance(e, exceptions.MethodNotAllowed):
            return make_response(405)
        if isinstance(e, exceptions.UnsupportedMediaType):
            return make_response(415)

        raise e
