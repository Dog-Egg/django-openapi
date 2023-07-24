import copy
import functools
import hashlib
import inspect
import itertools
import os
import sys
import typing as t
from http import HTTPStatus

import django.urls
from django.conf import settings
from django.http import HttpResponse
from django.http.response import HttpResponseBase, JsonResponse
from django.utils.functional import cached_property
from django.views.decorators.csrf import csrf_exempt

from django_openapi import schema
from django_openapi.exceptions import (
    ForbiddenError,
    MethodNotAllowedError,
    UnauthorizedError,
)
from django_openapi.parameter.parameters import MountPoint, Path
from django_openapi.permissions import BasePermission
from django_openapi.spec import Tag
from django_openapi.spec import utils as _spec
from django_openapi.utils.functional import make_model_schema, make_schema
from django_openapi_schema.spectools.objects import OpenAPISpec
from django_openapi_schema.utils import make_instance

from . import respond as _respond


def _get_id():
    frame = inspect.getframeinfo(sys._getframe(2))
    rv = "%s:%s" % (os.path.relpath(frame.filename), frame.lineno)
    return hashlib.md5(rv.encode()).hexdigest()


class OpenAPI:
    """
    :param info: OAS `Info Object <https://spec.openapis.org/oas/v3.0.3#info-object>`_，该对象提供有关 API 的元数据。

        默认值：

        .. code-block::

            {
                "title": "API Document",
                "version": "0.1.0"
            }

    """

    def __init__(
        self,
        *,
        info: t.Optional[dict] = None,
    ):
        self.__spec = OpenAPISpec(
            info=info
            if info is not None
            else {
                "title": "API Document",
                "version": "0.1.0",
            }
        )

        self.__id: str = _get_id()
        self.__urls: t.List[django.urls.URLPattern] = []
        self.__spec_endpoint = "/apispec_%s" % self.__id[:8]
        self.__resources: t.List[Resource] = []
        self.__append_url(self.__spec_endpoint, self.spec_view)
        self.respond = _respond.Respond

    @property
    def title(self):
        return self.__spec.title

    def add_resources(self, module):
        """从模块中查找资源并添加。"""
        from django_openapi.utils.project import find_resources

        for res in find_resources(module):
            self.add_resource(res)

    def add_resource(self, obj):
        if isinstance(obj, Resource):
            resource = obj
        else:
            resource = Resource.checkout(obj)
            if resource is None:
                raise ValueError("%s is not marked by %s." % (obj, Resource.__name__))

        assert resource.root is None
        resource.root = self

        self.__resources.append(resource)

        view = resource.as_view()
        self.__append_url(resource._django_path, view)

        self.__spec.add_path(resource._openapi_path, resource)

    def __append_url(self, path, *args, **kwargs):
        path = path.lstrip("/")
        self.__urls.append(django.urls.path(path, *args, **kwargs))

    @property
    def urls(self):
        return self.__urls

    def get_spec(self) -> dict:
        return self.__spec.to_dict()

    def spec_view(self, request):
        oas = self.get_spec()
        prefix = request.path[: -len(self.__spec_endpoint)]
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
    :param permission: 为其下的所有 `Operation` 设置权限。
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
        tags=None,
        permission: t.Union[BasePermission, t.Type[BasePermission], None] = None,
        view_decorators: t.Optional[list] = None,
        include_in_spec: bool = True,
    ):
        if not isinstance(path, Path):
            path = Path(path)
        self.__path: Path = path

        self.__operations: t.Dict[str, Operation] = {}
        self.tags = tags or []
        self._permission: t.Optional[BasePermission] = permission and make_instance(
            permission
        )
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

        for method, operation in self.__operations.items():
            for d in operation._view_decorators:
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
            self.__operations[method] = operation

            assert operation._resource is None
            operation._resource = self

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
            raise MethodNotAllowedError  # raise 405

        operation = self.__operations[method]
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
        for method, operation in self.__operations.items():
            result[method] = _spec.merge(
                {"parameters": spec.parse(self.__path)}, spec.parse(operation)
            )
        return result


class Operation:
    """
    :param include_in_spec: 是否将当前操作解析到 |OAS| 中，默认为 `True`。
    :param summary: 用于设置 |OAS| 操作对象摘要。
    :param permission: 设置操作请求权限。
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
        permission: t.Union[BasePermission, t.Type[BasePermission], None] = None,
        status_code: int = 200,
        view_decorators: t.Optional[list] = None,
    ):
        self._tags = tags or []
        self.__summary = summary
        self.__description = _spec.clean_commonmark(description)

        self.response_schema: t.Optional[schema.Schema] = None
        if response_schema is not None:
            self.response_schema = make_schema(response_schema)

        self.__deprecated = deprecated
        self.__include_in_spec = include_in_spec
        self.status_code = status_code
        self.__response_description = HTTPStatus(status_code).phrase
        self.__permission: t.Optional[BasePermission] = permission and make_instance(
            permission
        )
        self.__mountpoints: t.Dict[str, MountPoint] = {}
        self._resource: Resource = None  # type: ignore
        self._view_decorators = view_decorators or []

    def _get_tags(self, spec_id):
        tags = []
        for t in itertools.chain(self._resource.tags, self._tags):
            if isinstance(t, Tag):
                tags.append(t.name)
                _spec.Collection(spec_id).tags.add(t)
            else:
                tags.append(t)
        return tags

    def __parse_parameters(self, handler):
        for name, parameter in inspect.signature(handler).parameters.items():
            param = parameter.default
            if not isinstance(param, MountPoint):
                continue
            param.setup(self)
            self.__mountpoints[name] = param

    def parse_request(self, request):
        kwargs = {}
        for name, param in self.__mountpoints.items():
            kwargs[name] = param.parse_request(request)
        return kwargs

    def __call__(self, handler):
        self.__parse_parameters(handler)
        assert not hasattr(handler, "operation")
        handler.operation = self
        return handler

    @cached_property
    def _permission(self) -> t.Optional[BasePermission]:
        if self._resource._permission and self.__permission:
            return self._resource._permission & self.__permission
        return self._resource._permission or self.__permission

    def wrapped_invoke(self, handler, request) -> t.Tuple[t.Any, int]:
        # check permission
        if self._permission and not self._permission.has_permission(request):
            if request.user.is_authenticated:
                raise ForbiddenError
            raise UnauthorizedError

        kwargs = self.parse_request(request)
        rv = handler(**kwargs)
        if not isinstance(rv, HttpResponseBase) and self.response_schema:
            rv = self.response_schema.serialize(rv)
        return rv, self.status_code

    def __openapispec__(self, spec: OpenAPISpec):
        if not self.__include_in_spec:
            return

        return functools.reduce(
            _spec.merge,
            [
                {
                    "summary": self.__summary,
                    "description": self.__description,
                    # "tags": self._get_tags(123),
                    "deprecated": _spec.default_as_none(self.__deprecated, False),
                    "responses": {
                        self.status_code: {
                            "description": self.__response_description,
                            "content": {
                                "application/json": {
                                    "schema": self.response_schema
                                    and spec.parse(self.response_schema)
                                }
                            },
                        },
                    },
                    "security": self._permission and spec.parse(self._permission),
                },
                *(spec.parse(p) for p in self.__mountpoints.values()),
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
