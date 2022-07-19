import abc
import json as _json
from abc import ABC
from collections import UserString, ChainMap

from django.http import HttpRequest, JsonResponse

from openapi.http.exceptions import abort
from openapi.schema.schemas import Model, Schema
from openapi.typing import GeneralModelSchema, GeneralSchema
from openapi.utils import make_schema


class _Parser(abc.ABC):
    @abc.abstractmethod
    def parse_request(self, request: HttpRequest):
        raise NotImplemented


class _Parameters(_Parser, ABC):
    location = None

    def __init__(self, schema: GeneralModelSchema):
        self.schema: Model = make_schema(schema)


class Query(_Parameters):
    location = 'query'

    def parse_request(self, request):
        return self.schema.deserialize(request.GET)


class Cookie(_Parameters):
    location = 'cookie'

    def parse_request(self, request):
        return self.schema.deserialize(request.COOKIES)


class Header(_Parameters):
    location = 'header'

    def parse_request(self, request: HttpRequest):
        return self.schema.deserialize(request.headers)


class Path(UserString):
    def __init__(self, route, **kwargs):
        super().__init__(route)
        self.path_parameters = kwargs


class Body(_Parser):
    def __init__(self, schema: GeneralSchema, *, content_type=None):
        self.schema: Schema = make_schema(schema)

        if not content_type:
            self.content_type_list = ['application/json']
        else:
            self.content_type_list = [content_type] if isinstance(content_type, str) else content_type

    def parse_args(self, args):
        return self.schema.deserialize(args)

    def to_spec(self, spec_id):
        media_type = dict(
            schema=self.schema.to_spec(spec_id),
        )

        content = {x: media_type for x in self.content_type_list}

        return dict(
            content=content,
            required=True
        )

    def parse_request(self, request: HttpRequest):
        if request.content_type == 'application/json':
            try:
                data = _json.loads(request.body)
            except (_json.JSONDecodeError, TypeError):
                return abort(JsonResponse({'message': '不是一个JSON'}))
        else:
            # noinspection PyTypeChecker
            data = ChainMap(request.POST, request.FILES)

        return self.schema.deserialize(data)
