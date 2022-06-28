from django.http import JsonResponse

from openapi.core import API, Operation
from openapi.schemax import fields

books = [
    dict(id=1, title='解忧杂货铺', author='东野圭吾'),
    dict(id=2, title='岛上书店', author='加布瑞埃拉·泽文'),
]


class BookSchema(fields.Schema):
    id = fields.Integer(description='图书ID', example=1)
    title = fields.String(description='书名', example='三体')
    author = fields.String(description='作者', example='刘慈欣')


class ResponseSchema(fields.Schema):
    pass


class BooksAPI(API):
    @Operation(
        summary='获取图书列表',
        response_schema=fields.Schema.from_dict({'results': fields.List(BookSchema)})
    )
    def get(self):
        return JsonResponse({'results': books})

    @Operation(
        summary='创建图书',
        request_body=BookSchema.clone(include_fields=['title', 'author']),
    )
    def post(self, body):
        book = dict(id=len(books), **dict(body))
        books.append(book)
        return JsonResponse(book)


class BookAPI(API):
    @Operation(
        summary='获取图书详情',
        parameters={}
    )
    def get(self, book_id):
        pass

    def delete(self):
        pass
