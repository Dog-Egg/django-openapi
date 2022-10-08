from django.http.response import HttpResponseBase, HttpResponse, JsonResponse

from django_openapi import exceptions

__all__ = ['Respond']


class BaseRespond:
    def make_response(self, rv, status_code: int) -> HttpResponseBase:
        raise NotImplementedError

    def handle_error(self, e: Exception):
        raise NotImplementedError


class Respond(BaseRespond):
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
            return make_response(405)

        raise e
