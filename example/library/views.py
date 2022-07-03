import datetime

from openapi.http.exceptions import NotFound
from openapi.schemax.exceptions import DeserializationError
from . import models
from openapi.core import API, Operation
from openapi.schemax import fields, validators
from openapi.schemax.fields import Schema


class BookSchema(Schema):
    """图书"""

    class ValidateAuthorID(validators.Validator):
        def validate(self, value) -> None:
            try:
                models.Author.objects.get(pk=value)
            except models.Author.DoesNotExist:
                raise DeserializationError('ID不存在')

    id = fields.Integer(description='图书ID', example=1, required=True, serialize_only=True)
    title = fields.String(description='书名', example='三体', required=True)
    author_id = fields.Integer(description='作者ID', example=1, required=True, validators=[ValidateAuthorID()])
    created_at = fields.Datetime(description='创建时间', required=True, serialize_only=True)


class AuthorSchema(Schema):
    """作者"""

    id = fields.Integer(description='作者ID', example=1, required=True, serialize_only=True)
    name = fields.String(description='作者姓名', example='刘慈溪', required=True, strip=True)
    birthday = fields.Date(description='生日', required=True)


class BooksAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='获取图书列表',
        response=Schema.from_dict({'results': fields.List(BookSchema, required=True)})
    )
    def get(self, request):
        return {'results': models.Book.objects.all()}

    @Operation(
        summary='创建图书',
        body=BookSchema,
        response=BookSchema,
    )
    def post(self, request):
        body = request.data['body']
        return models.Book.objects.create(**body)


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
        deprecated=True,
    )
    def get(self, request, book_id):
        return self._get_book(book_id)

    def delete(self, request, book_id):
        self._get_book(book_id).delete()


class AuthorAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='作者列表',
        response=Schema.from_dict({'results': fields.List(AuthorSchema, required=True)})
    )
    def get(self, request):
        return {'results': models.Author.objects.all()}

    @Operation(
        summary='创建作者',
        body=AuthorSchema,
        response=AuthorSchema,
    )
    def post(self, request):
        instance = models.Author.objects.create(**request.data['body'])
        return instance
