import logging
import re
import typing
import uuid

import django.urls
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from openapi.enums import Location
from openapi.http.exceptions import HttpException, NotFound, MethodNotAllowed
from openapi.parameters import Path
from openapi.parameters.parse import ParameterParser
from openapi.router import join_path
from openapi.schema import schemas
from openapi.schema.exceptions import DeserializationError
from openapi.schema.schemas import Schema
from openapi.spec.schema import OperationObject, ResponsesObject, InfoObject, OpenAPIObject, PathsObject, \
    PathItemObject, ParameterObject, ResponseObject, MediaTypeObject, ComponentsObject
from openapi.typing import GeneralModelSchema
from openapi.utils import make_schema, merge
from openapi.ui import swagger_ui

logger = logging.getLogger(__name__)


class Operation:
    _HANDLER_OPERATION_KEY = '_operation'

    def __init__(
            self,
            *,
            tags: typing.List[str] = None,
            summary: str = None,
            description: str = None,
            response_schema: GeneralModelSchema = None,
            deprecated: bool = False,
            include_in_spec=True,
    ):
        self.tags = tags or []
        self.summary = summary
        self.description = description

        self.response_schema: Schema = response_schema and make_schema(response_schema)
        self.deprecated = deprecated
        self.include_in_spec = include_in_spec

        self.parser: ParameterParser = ...

    @classmethod
    def from_handler(cls, handler) -> 'Operation':
        if not hasattr(handler, cls._HANDLER_OPERATION_KEY):
            self = cls()
            self(handler)
        return getattr(handler, cls._HANDLER_OPERATION_KEY)

    def __call__(self, handler):
        self.parser = ParameterParser(handler)
        setattr(handler, self._HANDLER_OPERATION_KEY, self)
        return handler

    def wrap_invoke(self, handler, request, *args, **kwargs):
        kwargs.update(self.parser.parse_request(request))

        rv = handler(request, *args, **kwargs)

        if self.response_schema and not isinstance(rv, HttpResponse):
            rv = self.response_schema.serialize(rv)
        return rv

    def to_spec(self, spec_id, *, path_parameters) -> typing.Optional[OperationObject]:
        if not self.include_in_spec:
            return

        parameters = self.parser.get_spec_parameters()
        parameters.extend(path_parameters)

        return OperationObject(
            summary=self.summary,
            parameters=parameters,
            tags=self.tags,
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


class API(View):
    __path_parameters__: typing.Dict[str, Schema]

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
            self._deserialize_path_parameters(kwargs)

            operation = Operation.from_handler(handler)
            rv = operation.wrap_invoke(handler, request, *args, **kwargs)
        except HttpException as exc:
            return JsonResponse(exc.body, status=exc.status)
        except Exception:
            logger.exception('django-openapi')
            return JsonResponse({'message': 'Internal Server Error'}, status=500)

        if not isinstance(rv, HttpResponse):
            rv = JsonResponse(rv, safe=False)
        return rv

    def http_method_not_allowed(self, request, *args, **kwargs):
        raise MethodNotAllowed

    def _deserialize_path_parameters(self, kwargs):
        for name, schema in self.__path_parameters__.items():
            if name not in kwargs:
                continue
            try:
                kwargs[name] = schema.deserialize(kwargs[name])
            except DeserializationError:
                raise NotFound({'message': 'Not Found'})

    @Operation(include_in_spec=False)
    def options(self, *args, **kwargs):
        return super().options(*args, **kwargs)


class OpenAPI:
    def __init__(
            self,
            *,
            title: str,
            url_prefix=None,
            extra_specification=None,
            enable_swagger_ui=False,
    ):
        self._path_items: typing.Dict[str, PathItemObject] = {}
        self._spec_id = uuid.uuid4().hex
        self._title = title
        self._urls = []
        self._url_prefix = url_prefix or '/'
        self._extra_specification = extra_specification

        if enable_swagger_ui:
            self._register_django_url(self._join_path('api-spec'), self.api_spec, name=self._spec_id)
            self._register_django_url(self._join_path('swagger-ui'), swagger_ui(self._spec_id, title=self._title))

    def _register_django_url(self, *args, **kwargs):
        self._urls.append(django.urls.path(*args, **kwargs))

    def add_route(self, path: typing.Union[str, Path], apicls: typing.Type[API]):
        # noinspection PyTypeChecker
        apicls: typing.Type[API] = type(apicls.__name__, (apicls,), {'__path_parameters__': {}})
        if isinstance(path, Path):
            apicls.__path_parameters__.update(path.path_parameters)

        django_path, openapi_path, path_parameters_spec = self._parse_path(path)

        operations = {}
        for method, operation in self._parse_apicls(apicls).items():
            operation: Operation
            operations[method] = operation.to_spec(self._spec_id, path_parameters=path_parameters_spec)

        self._path_items[openapi_path] = PathItemObject(**operations)
        self._register_django_url(django_path, apicls.as_view())

    @property
    def urls(self):
        return self._urls, None, None

    @staticmethod
    def _parse_apicls(apicls: typing.Type[API]) -> typing.Dict[str, 'Operation']:
        operation_dict = {}
        for method in apicls.http_method_names:
            handler = getattr(apicls, method, None)
            if not handler:
                continue

            operation_dict[method] = Operation.from_handler(handler)

        return operation_dict

    def _join_path(self, path):
        return join_path(self._url_prefix, path)

    def _parse_path(self, path):
        if isinstance(path, Path):
            path_parameters = path.path_parameters
        else:
            path_parameters = None

        openapi_path = django_path = self._join_path(path)

        path_parameters_spec = []
        pattern = re.compile(r"{(?P<parameter>[^>]+)}")
        for match in pattern.finditer(openapi_path):
            (parameter,) = match.groups()

            if path_parameters and parameter in path_parameters:
                schema = path_parameters[parameter]
            else:
                schema = schemas.String()

            path_parameters_spec.append(ParameterObject(
                name=parameter,
                location=Location.PATH,
                required=True,
                description=schema.description,
                schema=schema.to_spec()
            ))
            django_path = django_path.replace(match.group(), '<%s>' % parameter)

        if not openapi_path.startswith('/'):
            openapi_path = '/' + openapi_path
        return django_path, openapi_path, path_parameters_spec

    def api_spec(self, request):
        spec = OpenAPIObject(
            info=InfoObject(title=self._title),
            paths=PathsObject(self._path_items),
            components=ComponentsObject(
                schemas=ComponentsObject.get_components(spec_id=self._spec_id, component_name='schemas')
            )
        ).serialize()

        if self._extra_specification:
            spec = merge(spec, self._extra_specification)

        json_dumps_params = dict(indent=2, ensure_ascii=False) if settings.DEBUG else {}
        try:
            return JsonResponse(spec, json_dumps_params=json_dumps_params)
        except TypeError:
            raise
