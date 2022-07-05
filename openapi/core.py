import logging
import re
import typing
import uuid

import django.urls
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from openapi.enums import Location
from openapi.http.exceptions import HttpException, NotFound, MethodNotAllowed
from openapi.parameters import Path
from openapi.parameters.parse import ParameterParser
from openapi.router import Router, RouterABC
from openapi.schemax import fields
from openapi.schemax.exceptions import DeserializationError
from openapi.schemax.fields import Field, Schema
from openapi.spec.schema import OperationObject, ResponsesObject, InfoObject, OpenAPIObject, PathsObject, \
    PathItemObject, ParameterObject, ResponseObject, MediaTypeObject, ComponentsObject
from openapi.typing import GeneralSchemaType
from openapi.utils import make_schema

logger = logging.getLogger(__name__)


class API(View):
    __path_parameters__: typing.Dict[str, Field] = {}
    tags: typing.List[str] = []

    @classmethod
    def as_view(cls, **initkwargs):
        return csrf_exempt(super().as_view(**initkwargs))

    def dispatch(self, request, *args, **kwargs):
        method_name = request.method.lower()
        if method_name in self.http_method_names:
            handler = getattr(self, method_name, self.http_method_not_allowed)
        else:
            handler = self.http_method_not_allowed

        # noinspection PyBroadException
        try:
            self._parse_path_parameters(kwargs)

            operation = Operation.from_handler(handler)
            rv = operation.invoke(handler, request, *args, **kwargs)

        except HttpException as exc:
            return JsonResponse(exc.body, status=exc.status)
        except Exception:
            logger.exception('django-openapi')
            return JsonResponse({'message': 'Internal Server Error'}, status=500)
        if not isinstance(rv, HttpResponse):
            rv = JsonResponse(rv or {}, safe=False)
        return rv

    def http_method_not_allowed(self, request, *args, **kwargs):
        raise MethodNotAllowed

    def _parse_path_parameters(self, kwargs):
        for name, field in self.__path_parameters__.items():
            if name in kwargs:
                try:
                    kwargs[name] = field.deserialize(kwargs[name])
                except DeserializationError:
                    raise NotFound({'message': 'Not Found'})


class OpenAPI(RouterABC):
    def __init__(self, *, title: str, prefix=None):
        self._path_items: typing.Dict[str, PathItemObject] = {}
        self._spec_id = uuid.uuid4().hex
        self.title = title
        self._router = Router(prefix=prefix)

    def add_route(self, route, apicls):
        # noinspection PyTypeChecker
        apicls: typing.Type[API] = type(apicls.__name__, (apicls,), {})

        if isinstance(route, Path):
            apicls.__path_parameters__.update(route.path_parameters)

        self._router.add_route(route, apicls)

    @property
    def urls(self):
        paths = []
        for route, apicls in self._router.get_routes():
            django_route, openapi_path, path_params = self._parse_route(route, apicls.__path_parameters__)

            operations = {}
            for method, operation in self._parse_apicls(apicls).items():
                operation: Operation
                operations[method] = operation.to_spec(self._spec_id, apicls=apicls, path_parameters=path_params)
            self._path_items[openapi_path] = PathItemObject(**operations)

            paths.append(django.urls.path(django_route, apicls.as_view()))
        return paths, None, None

    @staticmethod
    def _parse_apicls(apicls: typing.Type[API]) -> typing.Dict[str, 'Operation']:
        operation_dict = {}
        for method in apicls.http_method_names:
            handler = getattr(apicls, method, None)
            if not handler:
                continue

            operation_dict[method] = Operation.from_handler(handler)

        return operation_dict

    @staticmethod
    def _parse_route(route, path_parameters):
        pattern = re.compile(r"{(?P<parameter>[^>]+)}")
        path_params = []
        openapi_path = django_route = route
        for match in pattern.finditer(route):
            (parameter,) = match.groups()
            field = path_parameters.get(parameter, fields.String())
            path_params.append(ParameterObject(
                name=parameter,
                location=Location.PATH,
                required=True,
                description=field.description,
                schema=field.to_spec()
            ))
            django_route = django_route.replace(match.group(), '<%s>' % parameter)

        if not openapi_path.startswith('/'):
            openapi_path = '/' + openapi_path
        return django_route, openapi_path, path_params

    def get_spec(self, _):
        spec = OpenAPIObject(
            info=InfoObject(title=self.title),
            paths=PathsObject(self._path_items),
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
    _HANDLER_OPERATION_KEY = '_operation'

    def __init__(
            self,
            *,
            tags: typing.List[str] = None,
            summary: str = None,
            description: str = None,
            response: GeneralSchemaType = None,
            deprecated: bool = False,
    ):
        self.tags = tags or []
        self.summary = summary
        self.description = description

        self.response_schema: Schema = self._make_schema(response)
        self.deprecated = deprecated

        self.parser: ParameterParser = ...

    @classmethod
    def from_handler(cls, handler) -> 'Operation':
        if not hasattr(handler, cls._HANDLER_OPERATION_KEY):
            self = cls()
            self(handler)
        return getattr(handler, cls._HANDLER_OPERATION_KEY)

    @staticmethod
    def _make_schema(value: GeneralSchemaType) -> typing.Optional[Schema]:
        if not value:
            return
        return make_schema(value)

    def __call__(self, handler):
        self.parser = ParameterParser(handler)
        setattr(handler, self._HANDLER_OPERATION_KEY, self)
        return handler

    def invoke(self, handler, request, *args, **kwargs):
        kwargs.update(self.parser.parse_request(request))

        rv = handler(request, *args, **kwargs)

        if self.response_schema and not isinstance(rv, HttpResponse):
            rv = self.response_schema.serialize(rv)
        return rv

    def to_spec(self, spec_id, *, path_parameters, apicls: typing.Type[API]) -> OperationObject:
        tags = self.tags.copy()
        tags.extend(apicls.tags)

        parameters = self.parser.get_spec_parameters()
        parameters.extend(path_parameters)

        return OperationObject(
            summary=self.summary,
            parameters=parameters,
            tags=tags,
            deprecated=self.deprecated,
            request_body=self.parser.get_spec_request_body(spec_id),
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
