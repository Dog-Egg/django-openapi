import functools
import json
import logging
import re
import typing
import uuid

import django.urls
from django.http import HttpRequest, JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from openapi.enums import Location
from openapi.http.exceptions import BadRequest, HttpException, NotFound
from openapi.router import Router, RouterABC
from openapi.schemax import fields
from openapi.schemax.exceptions import DeserializationError
from openapi.schemax.fields import Field, Schema
from openapi.spec.schema import OperationObject, ResponsesObject, InfoObject, OpenAPIObject, PathsObject, \
    PathItemObject, ParameterObject, ResponseObject, RequestBodyObject, MediaTypeObject, ComponentsObject
from openapi.typing import GeneralSchemaType
from openapi.utils import make_instance

logger = logging.getLogger(__name__)

_HANDLER_OPERATION_KEY = '_operation'


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
    path_schema: typing.Dict[str, Field] = {}

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

        # noinspection PyBroadException
        try:
            self._parse_path_kwargs(kwargs)
            rv = handler(request, *args, **kwargs)
        except HttpException as exc:
            return JsonResponse(exc.body, status=exc.status)
        except Exception:
            logger.exception('django-openapi')
            return JsonResponse({'message': 'Internal Server Error'}, status=500)
        if not isinstance(rv, HttpResponse):
            rv = JsonResponse(rv or {}, safe=False)
        return rv

    def _parse_path_kwargs(self, kwargs):
        for name, field in self.path_schema.items():
            if name in kwargs:
                try:
                    kwargs[name] = field.deserialize(kwargs[name])
                except DeserializationError:
                    raise NotFound({'message': 'Not Found'})


class OpenAPI(RouterABC):
    def __init__(self, *, title: str, prefix=None):
        self.paths: typing.Dict[str, PathItemObject] = {}
        self._spec_id = uuid.uuid4().hex
        self.title = title
        self._router = Router(prefix=prefix)

    def add_route(self, *args, **kwargs):
        return self._router.add_route(*args, **kwargs)

    @property
    def urls(self):
        urls = []
        for route, api_cls in self._router.get_routes():
            route = self._handle_route(route, api_cls)
            urls.append(django.urls.path(route, api_cls.as_view()))
        return [urls, None, None]

    def _handle_route(self, route: str, api_cls: typing.Type[API]):
        operations = {}
        django_route, openapi_path, route_params = self._parse_route(route, api_cls)

        for method in api_cls.HTTP_METHODS:
            handler = getattr(api_cls, method, None)
            if not handler:
                continue

            op = getattr(handler, _HANDLER_OPERATION_KEY, None)
            if op is None:
                op = Operation()

            op_spec = op.to_spec(self._spec_id)
            op_spec.tags.extend(api_cls.tags)
            op_spec.parameters.extend(route_params)

            operations[method] = op_spec

        self.paths[openapi_path] = PathItemObject(**operations)
        return django_route

    @staticmethod
    def _parse_route(route, api_cls):
        pattern = re.compile(r"{(?P<parameter>[^>]+)}")
        params = []
        openapi_path = django_route = route
        for match in pattern.finditer(route):
            parameter, = match.groups()
            field = api_cls.path_schema.get(parameter)
            params.append(ParameterObject(
                name=parameter,
                location=Location.PATH,
                required=True,
                description=field and field.description,
                schema=field.to_spec() if field else fields.String().to_spec()
            ))
            django_route = django_route.replace(match.group(), '<%s>' % parameter)

        if not openapi_path.startswith('/'):
            openapi_path = '/' + openapi_path
        return django_route, openapi_path, params

    def get_spec(self, _):
        spec = OpenAPIObject(
            info=InfoObject(title=self.title),
            paths=PathsObject(self.paths),
            components=ComponentsObject(
                schemas=ComponentsObject.get_components(spec_id=self._spec_id, component_name='schemas')
            )
        ).serialize()
        try:
            return JsonResponse(spec)
        except TypeError:
            raise

    @staticmethod
    def swagger_ui(request):
        return render(request, 'swagger-ui.html')


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
            response: GeneralSchemaType = None,
            deprecated: bool = False,
    ):
        self.tags = tags
        self.summary = summary
        self.description = description

        self.query_schema: Schema = self._make_schema(query)
        self.cookie_schema: Schema = self._make_schema(cookie)
        self.header_schema: Schema = self._make_schema(header)
        self.body_schema: Schema = self._make_schema(body)
        self.response_schema: Schema = make_instance(response)
        self.deprecated = deprecated

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
            rv = handler(*args, **kwargs)
            if self.response_schema and not isinstance(rv, HttpResponse):
                rv = self.response_schema.serialize(rv)
            return rv

        setattr(wrapper, _HANDLER_OPERATION_KEY, self)
        return wrapper

    def _parse_request(self, request: HttpRequest):
        data = {}
        if self.body_schema:
            data['body'] = self._parse_request_body(request)
        request.data = data

    def _parse_request_query(self, request: HttpRequest):
        try:
            return self.query_schema.deserialize(request.GET)
        except DeserializationError as e:
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
        except DeserializationError as e:
            raise BadRequest(e.message)

    def to_spec(self, spec_id) -> OperationObject:
        parameters: typing.List[ParameterObject] = []
        for schema, location in [
            (self.query_schema, Location.QUERY),
            (self.cookie_schema, Location.COOKIE),
            (self.header_schema, Location.HEADER)
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
            deprecated=self.deprecated,
            request_body=RequestBodyObject(
                content={
                    'application/json': MediaTypeObject(
                        schema=self.body_schema and self.body_schema.to_spec(spec_id),
                    )
                },
                required=self.body_schema is not None
            ),
            responses=ResponsesObject(
                responses={
                    200: ResponseObject(
                        description='successful',
                        content={
                            'application/json': MediaTypeObject(
                                schema=self.response_schema and self.response_schema.to_spec(spec_id)
                            )
                        }
                    ),
                    500: ResponseObject(
                        description='error'
                    )
                })
        )
