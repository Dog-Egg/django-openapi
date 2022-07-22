import abc
import json as _json
from abc import ABC
from collections import UserString, ChainMap

from django.http import HttpRequest, JsonResponse

from openapi.http.exceptions import abort
from openapi.schema import schemas
from openapi.typing import GeneralModelSchema, GeneralSchema
from openapi.utils import make_schema


class _Parser(abc.ABC):
    @abc.abstractmethod
    def parse_request(self, request: HttpRequest):
        raise NotImplemented


class _Parameters(_Parser, ABC):
    location = None

    def __init__(self, schema: GeneralModelSchema):
        schema = make_schema(schema)
        if not isinstance(schema, schemas.Model):
            raise ValueError('Need a schema.Model object')
        self.schema = schema


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
    def __init__(self, _route_, **kwargs):
        super().__init__(_route_)
        self.path_parameters = kwargs

        if isinstance(_route_, Path):
            self.path_parameters.update(_route_.path_parameters)


class Body(_Parser):
    def __init__(self, schema: GeneralSchema, *, content_type=None):
        self.schema: schemas.SchemaABC = make_schema(schema)

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
