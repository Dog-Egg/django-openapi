from . import models
from openapi.http.exceptions import NotFound
from openapi.parameters import Query, Body
from openapi.schemax.exceptions import DeserializationError
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

    id = fields.Integer(description='图书ID', example=1, serialize_only=True)
    title = fields.String(description='书名', example='三体')
    tag = fields.String(description='标签', choices=['科幻', '喜剧', '传记'])
    author_id = fields.Integer(description='作者ID', example=1, validators=[ValidateAuthorID()])
    created_at = fields.Datetime(description='创建时间', serialize_only=True)


class AuthorSchema(Schema):
    """作者"""

    id = fields.Integer(description='作者ID', example=1, serialize_only=True)
    name = fields.String(description='作者姓名', example='刘慈溪', strip=True)
    birthday = fields.Date(description='生日')


class BooksAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='获取图书列表',
        response_schema={'results': fields.List(BookSchema)}
    )
    def get(self, request, query=Query(dict(tag=BookSchema.tag.copy_with(required=False)))):
        return {'results': models.Book.objects.filter(**query).all()}

    @Operation(
        summary='创建图书',
        response_schema=BookSchema,
    )
    def post(self, request, body=Body(BookSchema)):
        return models.Book.objects.create(**body)


class BookAPI(API):
    tags = ['图书馆']

    @staticmethod
    def _get_book(pk):
        try:
            return models.Book.objects.get(pk=pk)
        except models.Book.DoesNotExist:
            raise NotFound

    @Operation(
        summary='获取图书详情',
        response_schema=BookSchema,
        deprecated=True,
    )
    def get(self, request, book_id):
        return self._get_book(book_id)

    @Operation(response_schema=BookSchema)
    def put(self, request, book_id, body=Body(BookSchema)):
        book = self._get_book(book_id)
        for name, value in body.items():
            setattr(book, name, value)
        book.save()
        return book

    @Operation(response_schema=BookSchema)
    def patch(self, request, book_id, body=Body(BookSchema(required_fields=[]))):
        return self.put(request, book_id, body)

    def delete(self, request, book_id):
        self._get_book(book_id).delete()


class AuthorAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='作者列表',
        response_schema={'results': fields.List(AuthorSchema)}
    )
    def get(self, request):
        return {'results': models.Author.objects.all()}

    @Operation(
        summary='创建作者',
        response_schema=AuthorSchema,
    )
    def post(self, request, body=Body(AuthorSchema)):
        instance = models.Author.objects.create(**body)
        return instance
