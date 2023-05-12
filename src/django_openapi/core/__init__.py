import copy
import functools
import hashlib
import inspect
import itertools
import os
import re
import sys
import typing as t
import uuid
from collections import defaultdict
from http import HTTPStatus

import django.urls
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase, JsonResponse
from django.utils.functional import cached_property
from django.views.decorators.csrf import csrf_exempt

from django_openapi import schema
from django_openapi.exceptions import MethodNotAllowed, NotFound
from django_openapi.parameter.parameters import MountPoint, Path
from django_openapi.permissions import BasePermission
from django_openapi.spec import Tag
from django_openapi.spec import utils as _spec
from django_openapi.utils.functional import (
    make_instance,
    make_model_schema,
    make_schema,
)
from django_openapi_schema.spectools import OpenAPISpec

from . import respond as _respond


class OpenAPI:
    def __init__(
        self,
        *,
        title: str = "API Document",
        description: t.Optional[str] = None,
        version="0.1.0",
        security: t.Optional[t.List[t.Dict[str, t.List[str]]]] = None,
        security_schemes: t.Optional[dict] = None,
        respond=_respond.Respond,
    ):
        self._spec = OpenAPISpec()

        self._id: str = self.__get_id()
        self.title = title
        self._description = _spec.clean_commonmark(description)
        self._version = version
        self._urls: t.List[django.urls.URLPattern] = []
        self._security = security
        self._security_schemas = security_schemes
        self._spec_endpoint = "/apispec_%s" % self.id[:8]
        self._resources: t.List[Resource] = []
        self._append_url(self._spec_endpoint, self.spec_view)
        self.respond = respond

    @cached_property
    def id(self):
        return self._id

    @staticmethod
    def __get_id():
        # noinspection PyProtectedMember,PyUnresolvedReferences
        frame = inspect.getframeinfo(sys._getframe(2))
        rv = "%s:%s" % (os.path.relpath(frame.filename), frame.lineno)
        return hashlib.md5(rv.encode()).hexdigest()

    def add_resource(self, obj):
        if isinstance(obj, Resource):
            resource = obj
        else:
            resource = Resource.checkout(obj)
            if resource is None:
                raise ValueError("%s is not marked by %s." % (obj, Resource.__name__))

        assert resource.root is None
        resource.root = self

        self._resources.append(resource)

        view = resource.as_view()
        self._append_url(resource._django_path, view)

        self._spec.add_path(resource._openapi_path, resource)

    def _append_url(self, path, *args, **kwargs):
        path = path.lstrip("/")
        self._urls.append(django.urls.path(path, *args, **kwargs))

    @property
    def urls(self):
        return self._urls

    def get_spec(self) -> dict:
        return self._spec.to_dict()

    def spec_view(self, request):
        oas = self.get_spec()
        prefix = request.path[: -len(self._spec_endpoint)]
        if prefix:
            oas.update(servers=[{"url": prefix}])
        json_dumps_params = dict(indent=2, ensure_ascii=False) if settings.DEBUG else {}
        return JsonResponse(oas, json_dumps_params=json_dumps_params)

    def register_schema(self, schema):
        schema = make_model_schema(schema)
        # schema.to_spec(self.id, need_required_field=True, schema_id=uuid.uuid4().hex)


class Resource:
    """
    :param path: 资源 URL，必须以 "/" 开头。
    :param include_in_spec: 是否将当前资源解析到 |OAS| 中，默认为 `True`。
    """

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

    def __init__(
        self,
        path: t.Union[str, Path],
        *,
        path_parameters: t.Optional[t.Dict[str, schema.Schema]] = None,
        tags=None,
        permission=None,
        view_decorators: t.Optional[list] = None,
        include_in_spec: bool = True,
    ):
        if not isinstance(path, Path):
            path = Path(path)
        self.__path: Path = path

        self.operations: t.Dict[str, Operation] = {}
        self.path_parameters = path_parameters or {}
        self.tags = tags or []
        self.permission = permission
        self.root: t.Optional[OpenAPI] = None
        self.view_decorators = view_decorators or []
        self.include_in_spec = include_in_spec
        self.__view_function = None

    def __get_view_decorators(self):
        for d in self.view_decorators:
            yield d

        def operation_decorator(source_decorator, http_method):
            def decorator(view):
                @functools.wraps(view)
                def wrapper(request, *args, **kwargs):
                    if request.method == http_method:
                        return source_decorator(view)(request, *args, **kwargs)
                    return view(request, *args, **kwargs)

                return wrapper

            return decorator

        for method, operation in self.operations.items():
            for d in operation.view_decorators:
                yield operation_decorator(d, method.upper())

    __marked: t.Dict[t.Any, "Resource"] = {}

    def __call__(self, klass):
        if klass in self.__marked:
            raise ValueError(
                "%s has been marked by %s." % (klass, self.__class__.__name__)
            )
        self.__marked[klass] = self
        self.__klass = klass

        for method in self.HTTP_METHODS:
            handler = getattr(klass, method, None)
            if handler is None:
                continue

            operation = getattr(handler, "operation", None)
            if operation is None:
                operation = Operation()
                operation(handler)

            operation = copy.copy(operation)
            self.operations[method] = operation

            assert operation.resource is None
            operation.resource = self

        return klass

    @classmethod
    def checkout(cls, obj) -> t.Optional["Resource"]:
        try:
            return cls.__marked.get(obj)
        except TypeError:
            return None

    def as_view(self):
        if self.__view_function is None:

            @csrf_exempt
            def view(request, **kwargs) -> HttpResponseBase:
                respond = self.root.respond(request)  # type: ignore
                try:
                    rv, status_code = self._view(request, **kwargs)
                except Exception as exc:
                    return respond.handle_error(exc)
                return respond.make_response(rv, status_code)

            for decorator in self.__get_view_decorators():
                view = decorator(view)

            self.__view_function = view

        return self.__view_function

    def _view(self, request, **kwargs) -> t.Tuple[t.Any, int]:
        kwargs = self.__path.parse_kwargs(kwargs)  # raise path parameter 404

        method = request.method.lower()
        if method in self.HTTP_METHODS and hasattr(self.__klass, method):
            instance = (
                self.__klass()
                if self.__klass.__init__ is object.__init__
                else self.__klass(request, **kwargs)
            )
            handler = getattr(instance, method)
        else:
            raise MethodNotAllowed  # raise 405

        operation = self.operations[method]
        return operation.wrapped_invoke(handler, request)  # raise 401 403 ...

    @property
    def _django_path(self):
        return self.__path._django_path

    @property
    def _openapi_path(self):
        return self.__path._path

    def __openapispec__(self, spec: OpenAPISpec):
        if not self.include_in_spec:
            return
        result = {}
        for method, operation in self.operations.items():
            result[method] = _spec.merge(
                {"parameters": spec.parse(self.__path)}, spec.parse(operation)
            )
        return result


class Operation:
    """
    :param include_in_spec: 是否将当前操作解析到 |OAS| 中，默认为 `True`。
    :param summary: 用于设置 |OAS| 操作对象摘要。
    """

    def __init__(
        self,
        *,
        tags=None,
        summary: t.Optional[str] = None,
        description: t.Optional[str] = None,
        response_schema: t.Union[
            None, t.Type[schema.Model], t.Dict[str, schema.Schema], schema.Schema
        ] = None,
        deprecated: bool = False,
        include_in_spec: bool = True,
        permission=None,
        status_code: int = 200,
        view_decorators: t.Optional[list] = None,
    ):
        self._tags = tags or []
        self.summary = summary
        self.description = _spec.clean_commonmark(description)

        self.response_schema: t.Optional[schema.Schema] = None
        if response_schema is not None:
            self.response_schema = make_schema(response_schema)

        self.deprecated = deprecated
        self.include_in_spec = include_in_spec

        self.status_code = status_code
        self.response_description = HTTPStatus(status_code).phrase

        self._permission = permission

        self.resource: t.Optional[Resource] = None

        self._mountpoints: t.Dict[str, MountPoint] = {}
        self.view_decorators = view_decorators or []

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
    def permission(self) -> t.Optional[BasePermission]:
        perm = None
        assert self.resource
        for p in [self.resource.permission, self._permission]:
            if p is not None:
                p = make_instance(p)
                perm = p if perm is None else (perm & p)
        return perm

    def __parse_parameters(self, handler):
        for name, parameter in inspect.signature(handler).parameters.items():
            param = parameter.default
            if not isinstance(param, MountPoint):
                continue
            param.setup(self)
            self._mountpoints[name] = param

    def parse_request(self, request):
        kwargs = {}
        for name, param in self._mountpoints.items():
            kwargs[name] = param.parse_request(request)
        return kwargs

    def __call__(self, handler):
        self.__parse_parameters(handler)
        assert not hasattr(handler, "operation")
        handler.operation = self
        return handler

    def wrapped_invoke(self, handler, request) -> t.Tuple[t.Any, int]:
        # check permission
        if self.permission is not None:
            self.permission.check_permission(request)  # 401, 403

        kwargs = self.parse_request(request)
        rv = handler(**kwargs)
        if not isinstance(rv, HttpResponseBase) and self.response_schema:
            rv = self.response_schema.serialize(rv)
        return rv, self.status_code

    def __openapispec__(self, spec: OpenAPISpec):
        if not self.include_in_spec:
            return

        return functools.reduce(
            _spec.merge,
            [
                {
                    "summary": self.summary,
                    "description": self.description,
                    # "tags": self._get_tags(123),
                    "deprecated": _spec.default_as_none(self.deprecated, False),
                    "responses": {
                        self.status_code: {
                            "description": self.response_description,
                            "content": {
                                "application/json": {
                                    "schema": self.response_schema
                                    and spec.parse(self.response_schema)
                                }
                            },
                        },
                    },
                    # "security": self.permission
                    # and _spec.Skip(self.permission.to_spec, 123),
                },
                *(spec.parse(p) for p in self._mountpoints.values()),
            ],
        )


def make_response(rv, operation: Operation):
    # TODO: 需要根据定义的响应类型使用不同的 Response 对象。

    if isinstance(rv, HttpResponseBase):
        return rv

    if operation.response_schema is not None:
        rv = operation.response_schema.serialize(rv)

    if rv is None:
        rv = b""

    if isinstance(rv, (str, bytes)):
        return HttpResponse(rv, status=operation.status_code)

    return JsonResponse(rv, status=operation.status_code)
