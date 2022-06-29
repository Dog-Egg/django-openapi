import functools
import json
import logging
import re
import typing

from django.http import HttpRequest, JsonResponse, HttpResponse
from django.shortcuts import render
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from openapi.http.exceptions import BadRequest, HttpException
from openapi.schemax.exceptions import ValidationError
from openapi.schemax.fields import Field, Schema
from openapi.spec.schema import OperationObject, ResponsesObject, SchemaObject, InfoObject, OpenAPIObject, \
    ServerObject, PathsObject, PathItemObject, ParameterObject, ResponseObject, RequestBodyObject, MediaTypeObject, \
    ComponentsObject
from openapi.spec.utils import OPENAPI_SCHEMA_CONTAINER
from openapi.typing import GeneralSchemaType
from openapi.utils import make_instance

logger = logging.getLogger(__name__)


class API:
    request: HttpRequest

    HTTP_METHODS = [
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "head",
        "options",
        "trace",
    ]

    tags: typing.List[str] = []

    @classmethod
    def as_view(cls):
        @csrf_exempt
        def view(request, *args, **kwargs):
            self = cls()
            self.request = request
            return self.dispatch(request, *args, **kwargs)

        return view

    def dispatch(self, request, *args, **kwargs):
        handler = getattr(self, self.request.method.lower())
        try:
            rv = handler(request, *args, **kwargs)
        except HttpException as exc:
            return JsonResponse(exc.body, status=exc.status)
        if not isinstance(rv, HttpResponse):
            rv = JsonResponse(rv or {})
        return rv


class OpenAPI:
    def __init__(self):
        self.paths = {}
        self._urls = [
            path('spec', self._get_spec)
        ]

    def add_router(self, route, api_cls: typing.Type[API]):
        operations = {}
        openapi_path, route_params = self._parse_route(route)

        for method in api_cls.HTTP_METHODS:
            handler = getattr(api_cls, method, None)
            if not handler:
                continue

            op = getattr(handler, 'operation', None)
            if op is None:
                op = Operation()

            op_spec = op.to_spec()
            op_spec.tags.extend(api_cls.tags)
            op_spec.parameters.extend(route_params)

            operations[method] = op_spec

        self.paths[openapi_path] = PathItemObject(**operations)
        self._urls.append(path(route, api_cls.as_view()))

    @staticmethod
    def _parse_route(route):
        converter_to_type = {
            'int': SchemaObject.TypeEnum.INTEGER
        }

        pattern = re.compile(r"<(?:(?P<converter>[^>:]+):)?(?P<parameter>[^>]+)>")
        params = []
        openapi_path = route
        for match in pattern.finditer(route):
            converter, parameter = match.groups()
            params.append(ParameterObject(
                name=parameter,
                location=ParameterObject.LocationEnum.PATH,
                required=True,
                schema=SchemaObject(type=converter_to_type.get(converter, None))
            ))
            openapi_path = route.replace(match.group(), '{%s}' % parameter)

        if not openapi_path.startswith('/'):
            openapi_path = '/' + openapi_path
        return openapi_path, params

    @property
    def urls(self):
        return [self._urls, None, None]

    def _get_spec(self, _):
        spec = OpenAPIObject(
            info=InfoObject(title='This is title'),
            servers=[ServerObject(url='/api')],
            paths=PathsObject(self.paths),
            components=ComponentsObject(
                schemas=OPENAPI_SCHEMA_CONTAINER['schemas'],
            )
        ).serialize()
        try:
            return JsonResponse(spec)
        except TypeError:
            raise

    @staticmethod
    def swagger_ui(request):
        return render(request, 'swagger-ui.html')


FieldDictType = typing.Dict[str, Field]


class Operation:
    def __init__(
            self,
            *,
            tags: typing.List[str] = None,
            summary: str = None,
            description: str = None,
            query: GeneralSchemaType = None,
            cookie: GeneralSchemaType = None,
            header: GeneralSchemaType = None,
            body: GeneralSchemaType = None,
            response: GeneralSchemaType = None
    ):
        self.tags = tags
        self.summary = summary
        self.description = description

        self.query_schema: Schema = self._make_schema(query)
        self.cookie_schema: Schema = self._make_schema(cookie)
        self.header_schema: Schema = self._make_schema(header)
        self.body_schema: Schema = self._make_schema(body)
        self.response_schema: Schema = make_instance(response)

    @staticmethod
    def _make_schema(value: GeneralSchemaType) -> typing.Optional[Schema]:
        if not value:
            return
        if isinstance(value, dict):
            value = Schema.from_dict(value)
        return make_instance(value)

    def __call__(self, handler):
        @functools.wraps(handler)
        def wrapper(*args, **kwargs):
            for request in args:
                if isinstance(request, HttpRequest):
                    self._parse_request(request)
                    break
            return handler(*args, **kwargs)

        wrapper.operation = self
        return wrapper

    def _parse_request(self, request: HttpRequest):
        data = {}
        if self.body_schema:
            data['body'] = self._parse_request_body(request)
        request.data = data

    def _parse_request_query(self, request: HttpRequest):
        try:
            return self.query_schema.deserialize(request.GET)
        except ValidationError as e:
            raise BadRequest(e.message)

    def _parse_request_body(self, request: HttpRequest):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, TypeError):
            raise BadRequest
        if not isinstance(data, dict):
            raise BadRequest
        try:
            return self.body_schema.deserialize(data)
        except ValidationError as e:
            raise BadRequest(e.message)

    def to_spec(self):
        parameters = []
        for schema, location in [
            (self.query_schema, 'query'),
            (self.cookie_schema, 'cookie'),
            (self.header_schema, 'header')
        ]:
            if not schema:
                continue

            # noinspection PyProtectedMember
            for name, field in schema._fields.items():
                parameters.append(ParameterObject(
                    name=field.key,
                    location=location,
                    required=field.required,
                    description=field.description,
                    schema=field.to_spec(),
                ))

        return OperationObject(
            summary=self.summary,
            parameters=parameters,
            request_body=RequestBodyObject(content={
                'application/json': MediaTypeObject(
                    schema=self.body_schema and self.body_schema.to_spec(),
                )
            }),
            responses=ResponsesObject(
                responses={
                    '200': ResponseObject(
                        description='successful',
                        content={
                            'application/json': MediaTypeObject(
                                schema=self.response_schema and self.response_schema.to_spec()
                            )
                        }
                    )
                })
        )
