import json
import logging
import re
import typing

from django.http import HttpRequest, JsonResponse
from django.shortcuts import render
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from openapi.schemax.exceptions import ValidationError
from openapi.schemax.fields import Field, Schema
from openapi.spec.schema import OperationObject, ResponsesObject, SchemaObject, InfoObject, OpenAPIObject, \
    ServerObject, PathsObject, PathItemObject, ParameterObject, ResponseObject, RequestBodyObject, MediaTypeObject
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
        def view(request, **kwargs):
            self = cls()
            self.request = request
            return self.dispatch(**kwargs)

        return view

    def dispatch(self, **kwargs):
        query_kwargs = {}
        handler = getattr(self, self.request.method.lower())
        op = _operation_manager.get(handler)
        if op:
            try:
                query_kwargs = dict(op.query_schema.deserialize(self.request.GET))
            except ValidationError as e:
                return JsonResponse(e.message, status=400)

            if op.request_body:
                try:
                    body = op.request_body.deserialize(json.loads(self.request.body))
                except ValidationError as e:
                    return JsonResponse(e.message, status=400)
                else:
                    kwargs.update(body=body)
        return handler(**kwargs, **query_kwargs)


class _OperationManager:
    def __init__(self):
        self._operation_dict: typing.Dict[tuple, 'Operation'] = {}

    @staticmethod
    def _obj_to_ref(obj):
        return obj.__module__, obj.__qualname__

    def get(self, handler, default=None):
        return self._operation_dict.get(self._obj_to_ref(handler), default)

    def add(self, handler, operation: 'Operation'):
        self._operation_dict[self._obj_to_ref(handler)] = operation


_operation_manager = _OperationManager()


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

            op = _operation_manager.get(handler, Operation())
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
            paths=PathsObject(self.paths)
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
            parameters: FieldDictType = None,
            request_body: typing.Union[Schema, typing.Type[Schema]] = None,
            response_schema: typing.Union[Field, typing.Type[Field]] = None
    ):
        self.tags = tags
        self.summary = summary
        self.description = description
        self.parameters = parameters or {}
        self.query_schema = self._build_param_schemas('query')
        self.cookie_schema = self._build_param_schemas('cookie')
        self.header_schema = self._build_param_schemas('header')
        self.request_body: Schema = make_instance(request_body)
        self.response_schema: Schema = make_instance(response_schema)

    def _build_param_schemas(self, location) -> Schema:
        fields = {}
        for attr, field in self.parameters.items():
            if field.location == location:
                fields[attr] = field
        return Schema.from_dict(fields)()

    def __call__(self, handler):
        _operation_manager.add(handler, self)
        return handler

    def to_spec(self):
        parameters = []
        for attr, field in self.parameters.items():
            parameters.append(ParameterObject(
                name=field.name or attr,
                location=field.location,
                required=field.required,
                description=field.description,
                schema=field.to_spec(),
            ))

        return OperationObject(
            summary=self.summary,
            parameters=parameters,
            request_body=RequestBodyObject(content={
                'application/json': MediaTypeObject(
                    schema=self.request_body and self.request_body.to_spec(),
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
