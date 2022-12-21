import contextlib
import json
import typing
from abc import ABC

from django.http import HttpRequest
from django.utils.datastructures import MultiValueDict

from django_openapi.parameters.style import StyleParser
from django_openapi.spec import Example
from django_openapi.spec.utils import default_as_none, format_examples
from django_openapi.exceptions import BadRequest, UnsupportedMediaType, RequestArgsError
from django_openapi.schema import schemas
from django_openapi.schema.exceptions import ValidationError
from django_openapi.utils.functional import make_model_schema, make_schema


class BaseParameter:
    __limit__: int = 0

    def setup(self, operation):
        pass

    def parse_request(self, request: HttpRequest):
        raise NotImplementedError

    def to_spec(self, spec_id):
        raise NotImplementedError


class BaseRequestParameter(BaseParameter, ABC):
    def parse_request(self, request: HttpRequest):
        try:
            return self._parse_request(request)
        except ValidationError as exc:
            raise RequestArgsError(exc.format_errors())

    def _parse_request(self, request):
        raise NotImplementedError


class RequestParameter(BaseRequestParameter, ABC):
    location: typing.Optional[str]

    def __init__(self, schema):
        self.schema = make_model_schema(schema)
        self.parser = StyleParser({f.alias: f.style for f in self.schema.fields}, self.location)

    def to_spec(self, spec_id):
        spec = []
        for field in self.schema.fields:
            field: schemas.BaseSchema
            style, explode = field.style.get_style_and_explode(self.location)
            spec.append({
                'name': field.alias,
                'in': self.location,
                'required': default_as_none(field.required, False),
                'description': field.description,
                'schema': field.to_spec(spec_id),
                'style': style,
                'explode': explode,
                'allowEmptyValue': default_as_none(field.allow_blank, False),
                'examples': field.examples,
            })
        return dict(parameters=spec)


class Query(RequestParameter):
    """从 Request Query String 中解析请求参数。"""
    location = 'query'

    def _parse_request(self, request):
        return self.schema.deserialize(self.parser.parse(request.GET))


class Cookie(RequestParameter):
    """从 Request Cookie 中解析请求参数。"""
    location = 'cookie'

    def _parse_request(self, request):
        return self.schema.deserialize(self.parser.parse(request.COOKIES))


class Header(RequestParameter):
    """从 Request Header 中解析请求参数。"""
    location = 'header'

    def _parse_request(self, request: HttpRequest):
        return self.schema.deserialize(self.parser.parse(request.headers))


class FreeFormObject(schemas.BaseSchema):
    class Meta:
        data_type = 'object'

    def _serialize(self, obj):
        return obj

    def _deserialize(self, obj):
        return obj


class Body(BaseRequestParameter):
    """
    从 Request Body 中解析请求参数。

    :param schema: 参数结构。
    :param content_type: 可以处理的请求体数据类型，可以传列表来同时支持多个类型。

        目前仅支持:

        * application/json
        * multipart/form-data
        * application/x-www-form-urlencoded

        默认为 application/json。

    :param examples: 在 OAS 中展示请求示例。
    """
    __limit__ = 1

    def __init__(self, schema=None, *, content_type='application/json', examples: typing.List[Example] = None):
        self.schema = make_schema(schema) if schema is not None else FreeFormObject()
        self.content_types = [content_type] if isinstance(content_type, str) else content_type
        self._examples = format_examples(examples)
        supported_content_types = [
            'application/json',
            'multipart/form-data',
            'application/x-www-form-urlencoded',
        ]
        if not all(ct in supported_content_types for ct in self.content_types):
            raise ValueError(
                'The content_type currently supports only %s.' % ', '.join(
                    '%r' % item for item in supported_content_types))

    def to_spec(self, spec_id):
        schema_spec = self.schema.to_spec(spec_id, need_required_field=True)

        media_type = dict(
            schema=schema_spec,
            examples=self._examples,
        )

        content = {x: media_type for x in self.content_types}

        return dict(requestBody=dict(
            content=content,
            required=True
        ))

    def _parse_request(self, request: HttpRequest):
        if request.content_type not in self.content_types:
            raise UnsupportedMediaType

        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
            except (json.JSONDecodeError, TypeError):
                raise BadRequest
        else:
            # with _like_post_request(request) as request:
            # 先不处理，以后再说
            data = MultiValueDict()
            data.update(request.POST)
            data.update(request.FILES)
        return self.schema.deserialize(data)


@contextlib.contextmanager
def _like_post_request(request):
    # 因为 django 不处理 POST 以外的表单数据，所以这个修改一下方法名
    method = request.method
    try:
        request.method = 'POST'
        yield request
    finally:
        request.method = method
