from django.http import HttpResponse, JsonResponse

from openapi.core import API, operation
from openapi.parameters import StringParameter, IntegerParameter


class BooksAPI(API):
    tags = ['图书']

    @staticmethod
    @operation(
        parameters={
            'a': StringParameter,
            'b': IntegerParameter(default=None, description='变量B'),
        })
    def get(**kwargs):
        return JsonResponse(kwargs)

    @staticmethod
    @operation(
        request_body=...  # TODO
    )
    def post():
        return HttpResponse('ok')


class BookAPI(API):
    @staticmethod
    def get(book_id):
        return HttpResponse(book_id)

    @staticmethod
    def put(book_id):
        return HttpResponse(book_id)

    @staticmethod
    def delete(book_id):
        return HttpResponse(book_id)
