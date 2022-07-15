from django.contrib.auth.models import User

from . import models
from openapi.http.exceptions import NotFound
from openapi.parameters import Query, Body
from openapi.schema.exceptions import DeserializationError
from openapi.core import API, Operation
from openapi.schema import schemas, validators
from openapi.permissions import IsAuthenticated


class BookSchema(schemas.Model):
    """图书"""

    class ValidateAuthorID(validators.Validator):
        def validate(self, value) -> None:
            try:
                models.Author.objects.get(pk=value)
            except models.Author.DoesNotExist:
                raise DeserializationError('ID不存在')

    id = schemas.Integer(description='图书ID', example=1, serialize_only=True)
    title = schemas.String(description='书名', example='三体')
    tag = schemas.String(description='标签', enum=['科幻', '喜剧', '传记'])
    author_id = schemas.Integer(description='作者ID', example=1, validators=[ValidateAuthorID()])
    price = schemas.Float(description='价格', multiple_of=0.01, gt=0, lt=1000)
    created_at = schemas.Datetime(description='创建时间', serialize_only=True)


class AuthorSchema(schemas.Model):
    """作者"""

    id = schemas.Integer(description='作者ID', example=1, serialize_only=True)
    name = schemas.String(description='作者姓名', example='刘慈溪', strip=True)
    birthday = schemas.Date(description='生日')


class BooksAPI(API):
    @Operation(
        summary='获取图书列表',
        response_schema={'results': schemas.List(BookSchema)}
    )
    def get(self, request, query=Query(dict(tag=BookSchema.tag.copy_with(required=False)))):
        return {'results': models.Book.objects.filter(**query).all()}

    @Operation(
        summary='创建图书',
        response_schema=BookSchema,
        permission=IsAuthenticated
    )
    def post(self, request, body=Body(BookSchema)):
        return models.Book.objects.create(**body)


class BookAPI(API):
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
    @Operation(
        summary='作者列表',
        response_schema={'results': schemas.List(AuthorSchema)}
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


class ImageAPI(API):
    @Operation(
        summary='上传图片'
    )
    def post(self, request, body=Body(
        {
            'file': schemas.File(),
            'filename': schemas.String()
        },
        content_type='multipart/form-data'
    )):
        return {'filename': body['filename'], 'name': body['file'].name}


class UserSchema(schemas.Model):
    id = schemas.Integer(serialize_only=True)
    username = schemas.String()
    password = schemas.String(deserialize_only=True)


class UsersAPI(API):
    @Operation(
        response_schema=schemas.List(UserSchema),
        tags=['用户']
    )
    def get(self, request):
        return User.objects.all()
