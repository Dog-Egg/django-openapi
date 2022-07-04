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

    id = fields.Integer(description='图书ID', example=1, serialize_only=True)
    title = fields.String(description='书名', example='三体')
    tag = fields.String(description='标签', enum=['科幻', '喜剧', '传记'])
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
        query={
            'tag': BookSchema.tag.copy_with(required=False)
        },
        response=Schema.from_dict({'results': fields.List(BookSchema)})
    )
    def get(self, request):
        query = request.data['query']
        return {'results': models.Book.objects.filter(**query).all()}

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

    def _update(self, request, book_id):
        book = self._get_book(book_id)
        body = request.data['body']
        for name, value in body.items():
            setattr(book, name, value)
        book.save()
        return book

    @Operation(
        body=BookSchema,
        response=BookSchema,
    )
    def put(self, request, book_id):
        return self._update(request, book_id)

    @Operation(
        body=BookSchema(required_fields=[]),
        response=BookSchema,
    )
    def patch(self, request, book_id):
        return self._update(request, book_id)

    def delete(self, request, book_id):
        self._get_book(book_id).delete()


class AuthorAPI(API):
    tags = ['图书馆']

    @Operation(
        summary='作者列表',
        response=Schema.from_dict({'results': fields.List(AuthorSchema)})
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
