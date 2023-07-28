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
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseBase, JsonResponse
from django.utils.functional import cached_property
from django.views.decorators.csrf import csrf_exempt

from django_openapi import exceptions, schema
from django_openapi.parameter.parameters import MountPoint, Path
from django_openapi.permissions import BasePermission
from django_openapi.spec import Tag
from django_openapi.spec import utils as _spec
from django_openapi.utils.functional import make_model_schema, make_schema
from django_openapi_schema.spectools.objects import OpenAPISpec
from django_openapi_schema.utils import make_instance


def get_openapi_name():
    frame = inspect.getframeinfo(sys._getframe(2))
    rv = "%s:%s" % (os.path.relpath(frame.filename), frame.lineno)
    return hashlib.md5(rv.encode()).hexdigest()[:8]


def handle_RequestValidationError(
    e: exceptions.RequestValidationError, _
) -> HttpResponse:
    return JsonResponse(
        {"validation_errors": e.exc.format_errors()},
        status=400,
    )


class OpenAPI:
    """
    :param info: OAS `Info Object <https://spec.openapis.org/oas/v3.0.3#info-object>`_，该对象提供有关 API 的元数据。

        默认值：

        .. code-block::

            {
                "title": "API Document",
                "version": "0.1.0"
            }
    :param name: 如果需要对外分享 OAS 数据，建议设置该名称，它将作为 OAS 数据地址的一部分，而不是使用计算出的名称。

    """

    def __init__(
        self,
        *,
        info: t.Optional[dict] = None,
        name: t.Optional[str] = None,
    ):
        self.__spec = OpenAPISpec(
            info=info
            if info is not None
            else {
                "title": "API Document",
                "version": "0.1.0",
            }
        )

        self.__urls: t.List[django.urls.URLPattern] = []
        self.__spec_endpoint = "/apispec_%s" % (name or get_openapi_name())
        self.__append_url(self.__spec_endpoint, self.spec_view)
        self.__error_handlers: t.Dict[t.Type[Exception], t.Callable] = {
            exceptions.BadRequestError: lambda *_: HttpResponse(status=400),
            exceptions.UnauthorizedError: lambda *_: HttpResponse(status=401),
            exceptions.ForbiddenError: lambda *_: HttpResponse(status=403),
            exceptions.NotFoundError: lambda *_: HttpResponse(status=404),
            exceptions.MethodNotAllowedError: lambda *_: HttpResponse(status=405),
            exceptions.UnsupportedMediaTypeError: lambda *_: HttpResponse(status=415),
            exceptions.RequestValidationError: handle_RequestValidationError,
        }

    @property
    def title(self):
        return self.__spec.title

    def add_resources(self, module, **kwargs):
        """从模块中查找资源并添加。"""
        from django_openapi.utils.project import find_resources

        for res in find_resources(module):
            self.add_resource(res, **kwargs)

    def add_resource(self, obj, *, prefix="", tags=None):
        if prefix:
            if not prefix.startswith("/") or prefix.endswith("/"):
                raise ValueError(
                    'The prefix must start with a "/" and cannot end with a "/".'
                )

        if isinstance(obj, Resource):
            resource = obj
        else:
            resource = Resource.checkout(obj)
            if resource is None:
                raise ValueError("%s is not marked by %s." % (obj, Resource.__name__))

        resource = copy.copy(resource)

        def handle_error(exc, *args, **kwargs):
            for cls in inspect.getmro(exc.__class__):
                if cls in self.__error_handlers:
                    handler = self.__error_handlers[cls]
                    return handler(exc, *args, **kwargs)
            raise exc

        resource._handle_error = handle_error

        django_path, openapi_path = resource._path._resolve()
        view = resource.as_view()
        self.__append_url(prefix + django_path, view)
        self.__spec.add_path(
            prefix + openapi_path, self.__spec.parse(resource, tags=tags)
        )

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
            paths = oas.get("paths", {})
            for path in list(paths.keys()):
                paths[prefix + path] = paths[path]
                del paths[path]

        json_dumps_params = dict(indent=2, ensure_ascii=False) if settings.DEBUG else {}
        return JsonResponse(oas, json_dumps_params=json_dumps_params)

    def register_schema(self, schema):
        schema = make_model_schema(schema)
        # schema.to_spec(self.id, need_required_field=True, schema_id=uuid.uuid4().hex)

    def error_handler(self, e: t.Type[Exception]):
        def decorator(fn):
            self.__error_handlers[e] = fn
            return fn

        return decorator


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
        self._path: Path = path
        self.__operations: t.Dict[str, Operation] = {}
        self._tags: t.List = tags or []
        self._permission: t.Optional[BasePermission] = permission and make_instance(
            permission
        )
        self.__view_decorators = view_decorators or []
        self.__include_in_spec = include_in_spec
        self.__view_function = None
        self._handle_error: t.Callable[[Exception, HttpRequest], HttpResponseBase] = None  # type: ignore

    def __get_view_decorators(self):
        for d in self.__view_decorators:
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
                try:
                    rv, status_code = self.__view(request, **kwargs)
                except Exception as exc:
                    return self._handle_error(exc, request)
                return self.__make_response(rv, status_code)

            for decorator in self.__get_view_decorators():
                view = decorator(view)

            self.__view_function = view

        return self.__view_function

    def __make_response(self, rv, status: int):
        if isinstance(rv, HttpResponseBase):
            return rv
        if rv is None:
            rv = b""
        if isinstance(rv, (str, bytes)):
            return HttpResponse(rv, status=status)
        return JsonResponse(rv, status=status)

    def __view(self, request, **kwargs) -> t.Tuple[t.Any, int]:
        kwargs = self._path.parse_kwargs(kwargs)

        method = request.method.lower()
        if method in self.HTTP_METHODS and hasattr(self.__klass, method):
            instance = (
                self.__klass()
                if self.__klass.__init__ is object.__init__
                else self.__klass(request, **kwargs)
            )
            handler = getattr(instance, method)
        else:
            raise exceptions.MethodNotAllowedError

        operation = self.__operations[method]
        return operation.wrapped_invoke(handler, request)

    def __openapispec__(self, spec: OpenAPISpec, **kwargs):
        if not self.__include_in_spec:
            return
        result = {}
        for method, operation in self.__operations.items():
            result[method] = _spec.merge(
                {"parameters": spec.parse(self._path)}, spec.parse(operation, **kwargs)
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
        self.__tags = tags or []
        self.__summary = summary
        self.__description = _spec.clean_commonmark(description)

        self.response_schema: t.Optional[schema.Schema] = None
        if response_schema is not None:
            self.response_schema = make_schema(response_schema)

        self.__deprecated = deprecated
        self.__include_in_spec = include_in_spec
        self.__status_code = status_code
        self.__response_description = HTTPStatus(status_code).phrase
        self.__permission: t.Optional[BasePermission] = permission and make_instance(
            permission
        )
        self.__mountpoints: t.Dict[str, MountPoint] = {}
        self._resource: Resource = None  # type: ignore
        self._view_decorators = view_decorators or []

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
                raise exceptions.ForbiddenError
            raise exceptions.UnauthorizedError

        kwargs = self.parse_request(request)
        rv = handler(**kwargs)
        if not isinstance(rv, HttpResponseBase) and self.response_schema:
            rv = self.response_schema.serialize(rv)
        return rv, self.__status_code

    def __openapispec__(self, spec: OpenAPISpec, tags):
        if not self.__include_in_spec:
            return

        return functools.reduce(
            _spec.merge,
            [
                {
                    "summary": self.__summary,
                    "description": self.__description,
                    "tags": [
                        *self._resource._tags,
                        *self.__tags,
                        *(tags or []),
                    ],
                    "deprecated": _spec.default_as_none(self.__deprecated, False),
                    "responses": {
                        self.__status_code: {
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
