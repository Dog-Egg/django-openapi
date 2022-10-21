import copy
import functools
import hashlib
import inspect
import itertools
import os
import re
import sys
import typing
import uuid
from collections import defaultdict
from http import HTTPStatus

import django.urls
from django.conf import settings
from django.http import HttpRequest
from django.http.response import HttpResponseBase, JsonResponse
from django.utils.functional import cached_property
from django.views.decorators.csrf import csrf_exempt

from . import respond as _respond
from django_openapi.parameters.parameters import BaseParameter
from django_openapi.exceptions import NotFound, MethodNotAllowed
from django_openapi.parameters.style import StyleParser
from django_openapi.permissions import BasePermission
from django_openapi.schema import schemas
from django_openapi.schema.exceptions import ValidationError
from django_openapi.schema.schemas import BaseSchema
from django_openapi.utils.functional import make_schema, make_instance, make_model_schema
from django_openapi.spec import utils as _spec, Tag


class OpenAPI:
    def __init__(
            self,
            *,
            title: str = 'API Document',
            description: str = None,
            version='0.1.0',
            security: typing.List[typing.Dict[str, typing.List[str]]] = None,
            security_schemes: dict = None,
            respond=_respond.Respond,
    ):
        self._id: str = self.__get_id()
        self.title = title
        self._description = _spec.clean_commonmark(description)
        self._version = version
        self._urls: typing.List[django.urls.URLPattern] = []
        self._security = security
        self._security_schemas = security_schemes
        self._spec_endpoint = '/apispec_%s' % self.id[:8]
        self._resources: typing.List[Resource] = []
        self._append_url(self._spec_endpoint, self.spec_view)
        self.respond = respond

    @cached_property
    def id(self):
        return self._id

    @staticmethod
    def __get_id():
        # noinspection PyProtectedMember,PyUnresolvedReferences
        frame = inspect.getframeinfo(sys._getframe(2))
        rv = '%s:%s' % (os.path.relpath(frame.filename), frame.lineno)
        return hashlib.md5(rv.encode()).hexdigest()

    def add_resource(self, resource):
        assert resource.root is None
        resource.root = self

        self._resources.append(resource)

        view = resource.as_view()
        resource.view = view
        self._append_url(resource.django_path, view)

    def _append_url(self, path, *args, **kwargs):
        path = path.lstrip('/')
        self._urls.append(django.urls.path(path, *args, **kwargs))

    @property
    def urls(self):
        return self._urls

    def get_spec(self, request: HttpRequest = None) -> dict:
        if self._security_schemas:
            _spec.Collection(self.id).security = [{k: []} for k in self._security_schemas.keys()]

        spec = _spec.clean({
            'openapi': '3.0.3',
            'info': {
                'title': self.title,
                'version': self._version,
                'description': self._description,
            },
            'paths': _spec.Protect({r.openapi_path: r.to_spec(self.id) for r in self._resources}),
            'components': {
                'schemas': _spec.Collection(self.id).schemas,
                'securitySchemes': self._security_schemas,
            },
            'tags': _spec.Collection(self.id).tags.list(),
        })

        if request:
            prefix = request.path[:-len(self._spec_endpoint)]
            if prefix:
                spec.update(servers=[{'url': prefix}])

        if self._security is not None:
            spec.update(security=self._security)

        return spec

    def spec_view(self, request):
        spec = self.get_spec(request)
        json_dumps_params = dict(indent=2, ensure_ascii=False) if settings.DEBUG else {}
        return JsonResponse(spec, json_dumps_params=json_dumps_params)

    def register_schema(self, schema):
        schema = make_model_schema(schema)
        schema.to_spec(self.id, need_required_field=True, schema_id=uuid.uuid4().hex)


class Resource:
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
    view: typing.Callable

    def __init__(
            self,
            path: str,
            *,
            path_parameters: typing.Dict[str, BaseSchema] = None,
            tags=None,
            permission=None,
            view_decorators=None,
            include_in_spec=True,
    ):
        if not path.startswith('/'):
            raise ValueError('The path must start with a "/"')

        self.operations: typing.Dict[str, Operation] = {}
        self.path_parameters = path_parameters or {}
        self.tags = tags or []
        self.permission = permission
        self.root: typing.Optional[OpenAPI] = None
        self.view_decorators = view_decorators or []
        self.include_in_spec = include_in_spec
        self._parse_path(path)

        # path_kwargs_style_parser 必须在 parse_path() 后设置，parse_path() 会将为定义的路径参数添加到 path_parameters 中
        self._path_kwargs_style_parser = StyleParser({key: value.style for key, value in self.path_parameters.items()},
                                                     'path')

    def __call__(self, klass) -> 'Resource':
        for method in self.HTTP_METHODS:
            handler = getattr(klass, method, None)
            if handler is None:
                continue

            operation = getattr(handler, 'operation', None)
            if operation is None:
                operation = Operation()
                operation(handler)

            operation = copy.copy(operation)
            self.operations[method] = operation

            assert operation.resource is None
            operation.resource = self

        assert not hasattr(self, 'klass')
        self.klass = klass
        return self

    def _parse_path_parameters(self, kwargs):
        kwargs = self._path_kwargs_style_parser.parse(kwargs)
        for name, schema in self.path_parameters.items():
            if name not in kwargs:
                continue
            try:
                kwargs[name] = schema.deserialize(kwargs[name])
            except ValidationError:
                raise NotFound
        return kwargs

    def as_view(self):
        @csrf_exempt
        def view(request, *args, **kwargs) -> HttpResponseBase:
            respond = self.root.respond(request)  # type: ignore
            try:
                rv, status_code = self._view(request, *args, **kwargs)
            except Exception as exc:
                return respond.handle_error(exc)
            return respond.make_response(rv, status_code)

        for decorator in self.view_decorators:
            view = decorator(view)

        return view

    def _view(self, request, *args, **kwargs) -> typing.Tuple[typing.Any, int]:
        kwargs = self._parse_path_parameters(kwargs)  # raise path parameter 404

        method = request.method.lower()
        if method in self.HTTP_METHODS and hasattr(self.klass, method):
            instance = self.klass() if self.klass.__init__ is object.__init__ else self.klass(request, *args, **kwargs)
            handler = getattr(instance, method)
        else:
            raise MethodNotAllowed  # raise 405

        operation = self.operations[method]
        return operation.wrapped_invoke(handler, request)  # raise 401 403 ...

    def _parse_path(self, path):
        assert path.startswith('/')
        openapi_path = django_path = path

        path_parameters_spec = []
        pattern = re.compile(r"{(?P<parameter>.*)}")
        for match in pattern.finditer(openapi_path):
            (parameter,) = match.groups()

            if parameter in self.path_parameters:
                schema = self.path_parameters[parameter]
            else:
                schema = schemas.String()
                self.path_parameters[parameter] = schema

            style, explode = schema.style.get_style_and_explode('path')
            path_parameters_spec.append({
                'name': parameter,
                'in': 'path',
                'required': True,
                'description': schema.description,
                'schema': schema.to_spec(),
                'style': style,
                'explode': explode,
            })

            if isinstance(schema, schemas.Path):
                placeholder = '<path:%s>'
            else:
                placeholder = '<%s>'
            django_path = django_path.replace(match.group(), placeholder % parameter)

        self.django_path = django_path
        self.openapi_path = openapi_path
        self.path_parameters_spec = path_parameters_spec

    def to_spec(self, spec_id):
        if not self.include_in_spec:
            return
        spec = {}
        for method, operation in self.operations.items():
            spec[method] = _spec.merge({'parameters': self.path_parameters_spec}, operation.to_spec(spec_id))
        return spec


class Operation:
    def __init__(
            self,
            *,
            tags=None,
            summary: str = None,
            description: str = None,
            response_schema=None,
            deprecated: bool = False,
            include_in_spec=True,
            permission=None,
            status_code: int = 200
    ):
        self._tags = tags or []
        self.summary = summary
        self.description = description

        self.response_schema: BaseSchema = response_schema and make_schema(response_schema)
        self.deprecated = deprecated
        self.include_in_spec = include_in_spec

        self.status_code = status_code
        self.response_description = HTTPStatus(status_code).phrase

        self._permission = permission

        self.resource: typing.Optional[Resource] = None

        self.parameters: typing.Dict[str, BaseParameter] = {}

    def _get_tags(self, spec_id):
        tags = []
        for t in itertools.chain(self.resource.tags, self._tags):
            if isinstance(t, Tag):
                tags.append(t.name)
                _spec.Collection(spec_id).tags.add(t)
            else:
                tags.append(t)
        return tags

    @cached_property
    def permission(self) -> typing.Optional[BasePermission]:
        perm = None
        assert self.resource
        for p in [self.resource.permission, self._permission]:
            if p is not None:
                p = make_instance(p)
                perm = p if perm is None else (perm & p)
        return perm

    def parse_parameters(self, handler):
        counter = defaultdict(int)
        for name, parameter in inspect.signature(handler).parameters.items():
            param = parameter.default
            if not isinstance(param, BaseParameter):
                continue
            param.setup(self)
            self.parameters[name] = param

            p_cls = type(param)
            if param.__limit__:
                counter[p_cls] += 1
                if counter[p_cls] > param.__limit__:
                    raise ValueError(f'{p_cls.__name__} define {p_cls.__limit__} at most')

    def parse_request(self, request):
        kwargs = {}
        for name, param in self.parameters.items():
            kwargs[name] = param.parse_request(request)
        return kwargs

    def __call__(self, handler):
        self.parse_parameters(handler)
        assert not hasattr(handler, 'operation')
        handler.operation = self
        return handler

    def wrapped_invoke(self, handler, request) -> typing.Tuple[typing.Any, int]:
        # check permission
        self.permission is not None and self.permission.check_permission(request)  # 401, 403

        kwargs = self.parse_request(request)
        rv = handler(**kwargs)
        if not isinstance(rv, HttpResponseBase) and self.response_schema:
            rv = self.response_schema.serialize(rv)
        return rv, self.status_code

    def to_spec(self, spec_id):
        if not self.include_in_spec:
            return

        return functools.reduce(_spec.merge, [
            {
                'summary': self.summary,
                'description': self.description,
                'tags': self._get_tags(spec_id),
                'deprecated': _spec.default_as_none(self.deprecated, False),
                'responses': {
                    self.status_code: {
                        'description': self.response_description,
                        'content': {
                            'application/json': {
                                'schema': self.response_schema and self.response_schema.to_spec(spec_id)
                            }
                        }
                    },
                },
                'security': self.permission and _spec.Skip(self.permission.to_spec, spec_id)
            },
            *(x.to_spec(spec_id) for x in self.parameters.values())
        ])
