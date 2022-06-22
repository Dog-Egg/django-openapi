import functools
import inspect
import typing

import marshmallow
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from openapi.schema.properties import Property, Schema
from openapi.spec.schema import OperationObject, ResponsesObject, RequestBodyObject, MediaTypeObject, SchemaObject


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
        op = Operation.manager.get(handler)
        if op:
            try:
                query_kwargs: dict = op.schema.deserialize(self.request.GET)
            except marshmallow.ValidationError as e:
                return JsonResponse(e.normalized_messages(), status=400)
        return handler(**kwargs, **query_kwargs)


class _OperationManager:
    def __init__(self):
        self._operation_dict: typing.Dict[tuple, 'Operation'] = {}

    @staticmethod
    def _obj_to_ref(obj):
        return obj.__module__, obj.__qualname__

    def get(self, handler, default=None):
        return self._operation_dict.get(self._obj_to_ref(handler), default)

    def add(self, handler, operation_: 'Operation'):
        self._operation_dict[self._obj_to_ref(handler)] = operation_


class Operation:
    manager = _OperationManager()

    def __init__(
            self,
            *,
            tags: typing.List[str] = None,
            summary: str = None,
            description: str = None,
            parameters: typing.Dict[str, typing.Union[Property, typing.Type[Property]]] = None,
            request_body=None,
    ):
        self.tags = tags
        self.summary = summary
        self.description = description

        self.parameters: typing.Dict[str, Property] = {}
        if parameters:
            for name, param in parameters.items():
                if inspect.isclass(param):
                    param = param()

                if param.name is None:
                    param.name = name

                self.parameters[name] = param

        self.schema: Schema = Schema.from_dict(self.parameters)()

    def __call__(self, handler):
        self.manager.add(handler, self)

        @functools.wraps(handler)
        def wrapper(*args, **kwargs):
            return handler(*args, **kwargs)

        return wrapper

    def to_spec(self):
        return OperationObject(
            tags=self.tags or [],
            parameters=[p.to_spec() for p in self.parameters.values()],
            responses=ResponsesObject({}),
            request_body=RequestBodyObject(
                content={
                    'application/json': MediaTypeObject(
                        schema=SchemaObject(
                            type='object'
                        )
                    ),
                }
            ),
        )


operation = Operation
