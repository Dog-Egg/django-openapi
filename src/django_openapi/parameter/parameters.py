import abc
import contextlib
import json
import re
import typing as t

from django.http import HttpRequest
from django.utils.datastructures import MultiValueDict

from django_openapi import schema as _schema
from django_openapi.exceptions import (
    BadRequestError,
    NotFoundError,
    RequestArgsError,
    UnsupportedMediaTypeError,
)
from django_openapi.spec.utils import default_as_none
from django_openapi.utils.functional import make_model_schema, make_schema
from django_openapi_schema.spectools.utils import clean_commonmark

from .style import Style, StyleHandler


class Path:
    """
    :param path: 到单个端点的相对路径，必须以正斜杠 ``/`` 开头。该路径将用于构建完整的 URL。支持 `路径模版 <https://spec.openapis.org/oas/v3.0.3#path-templating>`_ 。
    :param param_schemas: 路径中如果存在变量，则可以使用该值指定参数结构。变量默认结构为 `String <django_openapi.schema.String>`。
    :param param_styles: 路径中如果存在变量，则可以使用该值指定参数样式。
    """

    def __init__(
        self,
        path: str,
        /,
        param_schemas: t.Optional[t.Dict[str, _schema.Schema]] = None,
        param_styles: t.Union[t.Dict[str, Style], None] = None,
    ):
        if not path.startswith("/"):
            raise ValueError('The path must start with a "/".')
        self._path = django_path = path
        self.__param_schemas: t.Dict[str, _schema.Schema] = {}
        self.__param_style_handlers: t.Dict[str, StyleHandler] = {}

        param_schemas = param_schemas or {}
        pattern = re.compile(r"{(?P<param>.*)}")
        for match in pattern.finditer(self._path):
            (param,) = match.groups()
            if param not in param_schemas:
                param_schemas[param] = _schema.String()
            schema = param_schemas[param]
            self.__param_schemas[param] = schema

            if isinstance(schema, _schema.Path):
                placeholder = "<path:%s>"
            else:
                placeholder = "<%s>"
            django_path = django_path.replace(match.group(), placeholder % param)

            # style
            style = (param_styles or {}).get(param) or Style("simple", False)
            self.__param_style_handlers[param] = StyleHandler(style, schema, "path")

        self._django_path = django_path

    def parse_kwargs(self, kwargs: dict):
        for param, schema in self.__param_schemas.items():
            if param not in kwargs:
                continue

            value = self.__param_style_handlers[param].handle(kwargs[param])
            try:
                kwargs[param] = schema.deserialize(value)
            except _schema.ValidationError:
                raise NotFoundError
        return kwargs

    def __openapispec__(self, spec):
        result = []
        for param, schema in self.__param_schemas.items():
            style = self.__param_style_handlers[param].style
            result.append(
                {
                    "name": param,
                    "in": "path",
                    "required": True,
                    "schema": spec.parse(schema),
                    "style": style.style,
                    "explode": style.explode,
                }
            )
        return result


class MountPoint(abc.ABC):
    def setup(self, operation):
        pass

    @abc.abstractmethod
    def parse_request(self, request: HttpRequest):
        pass


class BaseRequestParameter(MountPoint, abc.ABC):
    def parse_request(self, request: HttpRequest) -> t.Any:
        try:
            return self._parse_request(request)
        except _schema.ValidationError as exc:
            raise RequestArgsError(exc.format_errors())

    @abc.abstractmethod
    def _parse_request(self, request):
        pass


class RequestParameter(BaseRequestParameter, abc.ABC):
    location: t.Optional[str]

    def __init__(
        self,
        schema: t.Union[_schema.Model, t.Dict[str, _schema.Schema]],
        /,
        param_styles: t.Optional[t.Dict[str, Style]] = None,
    ):
        self._schema = make_model_schema(schema)

        self.__param_styles = param_styles or {}
        self.__param_style_handlers: t.Dict[_schema.Schema, StyleHandler] = {}
        for field in self._schema._fields.values():
            style = self.__get_style(field)
            self.__param_style_handlers[field] = StyleHandler(
                style, field, self.location
            )

    def __get_style(self, field: _schema.Schema) -> Style:
        if field._name in self.__param_styles:
            return self.__param_styles[field._name]

        if self.location == "query":
            return Style("form", True)
        elif self.location == "cookie":
            return Style("form", False)
        elif self.location == "header":
            return Style("simple", False)
        raise NotImplementedError(self.location)

    def _handle_style(self, data):
        rv = {}
        for field in self._schema._fields.values():
            handler = self.__param_style_handlers[field]
            v = handler.handle(data)
            if v is not handler.empty:
                rv[field._alias] = v
        return rv

    def __openapispec__(self, spec):
        result = []
        for field in self._schema._fields.values():
            style = self.__get_style(field)
            result.append(
                {
                    "name": field._alias,
                    "in": self.location,
                    "required": default_as_none(field._required, False),
                    "description": field.options["description"] or None,
                    "schema": spec.parse(field),
                    "style": style.style,
                    "explode": style.explode,
                    # "allowEmptyValue": default_as_none(field.allow_blank, False),
                    # "examples": field.examples,
                }
            )
        return dict(parameters=result)


class Query(RequestParameter):
    location = "query"

    def _parse_request(self, request: HttpRequest):
        return self._schema.deserialize(self._handle_style(request.GET))


class Cookie(RequestParameter):
    location = "cookie"

    def _parse_request(self, request: HttpRequest):
        return self._schema.deserialize(self._handle_style(request.COOKIES))


class Header(RequestParameter):
    location = "header"

    def _parse_request(self, request: HttpRequest):
        return self._schema.deserialize((request.headers))


class MediaType:
    def __init__(self, schema) -> None:
        self.__schema = make_schema(schema)

    def __openapispec__(self, spec):
        return {
            "schema": spec.parse(self.__schema),
        }

    def parse_request(self, request: HttpRequest):
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
            except (json.JSONDecodeError, TypeError):
                raise BadRequestError
        else:
            combine = MultiValueDict()
            combine.update(request.POST)
            combine.update(request.FILES)
            if isinstance(self.__schema, _schema.Model):
                data = {}
                for field in self.__schema._fields.values():
                    k = field._alias
                    if k in combine:
                        data[k] = (
                            combine.getlist(k)
                            if isinstance(field, _schema.List)
                            else combine[k]
                        )
            else:
                data = dict(combine.items())
        return self.__schema.deserialize(data)


class Body(BaseRequestParameter):
    """
    :param content_type: 请求体内容类型，默认是: application/json。也可以设置为列表，以支持多种请求体类型。
    """

    def __init__(
        self,
        schema,
        *,
        # content: t.Optional[t.Dict[str, MediaType]] = None,
        content_type: t.Union[str, t.List[str]] = "application/json",
        description: str = "",
        # required: bool = True,
    ):
        schema = make_schema(schema)

        if isinstance(content_type, str):
            content_type_list = [content_type]
        else:
            content_type_list = content_type

        self.__content: t.Dict[str, MediaType] = {
            item: MediaType(schema) for item in content_type_list
        }

        self.__required = True
        self.__description = clean_commonmark(description)

    def __openapispec__(self, spec):
        return {
            "requestBody": {
                "required": self.__required,
                "description": self.__description,
                "content": {c: spec.parse(m) for c, m in self.__content.items()},
            }
        }

    def _parse_request(self, request: HttpRequest):
        if request.content_type not in self.__content:
            raise UnsupportedMediaTypeError
        return self.__content[request.content_type].parse_request(request)


@contextlib.contextmanager
def _like_post_request(request):
    # 因为 django 不处理 POST 以外的表单数据，所以这个修改一下方法名
    method = request.method
    try:
        request.method = "POST"
        yield request
    finally:
        request.method = method
