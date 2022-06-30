import datetime

from openapi.http.exceptions import NotFound
from . import models
from .schemas import BookSchema, AuthorSchema
from openapi.core import API, Operation
from openapi.schemax import fields


class BooksAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='获取图书列表',
        response=fields.Schema.from_dict({'results': fields.List(BookSchema, required=True)})
    )
    def get(self, request):
        return {'results': models.Book.objects.all()}

    @Operation(
        summary='创建图书',
        body=BookSchema.clone(include=[
            BookSchema.title.name,
            BookSchema.author_id.name,
        ]),
        response=BookSchema,
    )
    def post(self, request):
        body = request.data['body']
        return models.Book.objects.create(**body, created_at=datetime.datetime.now())


class BookAPI(API):
    tags = ['图书馆']

    path_schema = {
        'book_id': BookSchema.id
    }

    @staticmethod
    def _get_book(pk):
        try:
            return models.Book.objects.get(pk=pk)
        except models.Book.DoesNotExist:
            raise NotFound

    @Operation(
        summary='获取图书详情',
        response=BookSchema,
    )
    def get(self, request, book_id):
        return self._get_book(book_id)

    def delete(self, request, book_id):
        self._get_book(book_id).delete()


class AuthorAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='作者列表',
        response=fields.Schema.from_dict({'results': fields.List(AuthorSchema, required=True)})
    )
    def get(self, request):
        return {'results': models.Author.objects.all()}

    @Operation(
        summary='创建作者',
        body=AuthorSchema.clone(exclude=[AuthorSchema.id.name]),
        response=AuthorSchema,
    )
    def post(self, request):
        instance = models.Author.objects.create(**request.data['body'])
        return instance
