from datetime import datetime

from . import models
from .schemas import BookSchema, AuthorSchema
from openapi.core import API, Operation
from openapi.schemax import fields

books = [
    dict(id=1, title='解忧杂货铺', author='东野圭吾', created_at=datetime(2000, 1, 8, 9, 10)),
    dict(id=2, title='岛上书店', author='加布瑞埃拉·泽文', created_at=datetime(2005, 4, 5, 7, 10)),
]
book_pk = len(books) + 1


class BooksAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='获取图书列表',
        response=fields.Schema.from_dict({'results': fields.List(BookSchema, required=True)})
    )
    def get(self, request):
        return {'results': books}

    @Operation(
        summary='创建图书',
        body=BookSchema.clone(include=['title', 'author']),
        response=BookSchema,
    )
    def post(self, request):
        global book_pk
        book = dict(id=book_pk, **dict(request.data['body']))
        book_pk += 1
        books.append(book)
        return book


class BookAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='获取图书详情',
    )
    def get(self, request, book_id):
        pass

    @staticmethod
    def delete(request, book_id):
        return


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
        body=AuthorSchema.clone(exclude=['id']),
        response=AuthorSchema,
    )
    def post(self, request):
        instance = models.Author.objects.create(**dict(request.data['body']))
        return instance
