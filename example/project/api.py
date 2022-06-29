from openapi.core import API, Operation
from openapi.schemax import fields

books = [
    dict(id=1, title='解忧杂货铺', author='东野圭吾'),
    dict(id=2, title='岛上书店', author='加布瑞埃拉·泽文'),
]
book_pk = len(books) + 1


class BookSchema(fields.Schema):
    id = fields.Integer(description='图书ID', example=1)
    title = fields.String(description='书名', example='三体', required=True)
    author = fields.String(description='作者', example='刘慈欣', required=True)


class ResponseSchema(fields.Schema):
    pass


class BooksAPI(API):
    @Operation(
        summary='获取图书列表',
        response=fields.Schema.from_dict({'results': fields.List(BookSchema)})
    )
    def get(self, request):
        return {'results': books}

    @Operation(
        summary='创建图书',
        body=BookSchema.clone(include=['title', 'author']),
    )
    def post(self, request):
        global book_pk
        book = dict(id=book_pk, **dict(request.data['body']))
        book_pk += 1
        books.append(book)
        return book


class BookAPI(API):
    @Operation(
        summary='获取图书详情',
    )
    def get(self, request, book_id):
        pass

    @staticmethod
    @Operation()
    def delete(request, book_id):
        return
