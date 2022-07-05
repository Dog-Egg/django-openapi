import inspect
import json
import typing

from django.http import HttpRequest

from ._parameters import _Parameters, Body, Query, Cookie, Header
from openapi.spec.schema import ParameterObject, RequestBodyObject, MediaTypeObject
from ..http.exceptions import BadRequest
from ..schemax.exceptions import DeserializationError


class ParameterParser:
    def __init__(self, function):
        self._parameter_dict: typing.Dict[str, _Parameters] = {}
        for name, parameter in inspect.signature(function).parameters.items():
            param = parameter.default
            if isinstance(param, _Parameters):
                self._parameter_dict[name] = param

    def get_spec_parameters(self):
        params: typing.List[ParameterObject] = []

        for param_name, param in self._parameter_dict.items():
            if isinstance(param, Body):
                continue

            # noinspection PyProtectedMember
            for field_name, field in param.schema._fields.items():
                params.append(ParameterObject(
                    name=field.key or field_name,
                    location=param.location,
                    required=field.required,
                    description=field.description,
                    schema=field.to_spec()
                ))
        return params

    def get_spec_request_body(self, spec_id=None):
        for name, param in self._parameter_dict.items():
            if isinstance(param, Body):
                param: _Parameters
                schema = param.schema
                return RequestBodyObject(
                    content={
                        'application/json': MediaTypeObject(
                            schema=schema.to_spec(spec_id),
                        )
                    },
                    required=True
                )

    def parse_request(self, request: HttpRequest):
        functions = {
            Query: _get_request_query,
            Cookie: _get_request_cookie,
            Header: _get_request_header,
            Body: _get_request_body,
        }

        rv = {}
        for name, param in self._parameter_dict.items():
            fn = functions[param.__class__]
            try:
                rv[name] = param.deserialize(fn(request))
            except DeserializationError as exc:
                raise BadRequest(exc.message)
        return rv


def _get_request_query(request):
    return request.GET


def _get_request_cookie(request):
    return request.COOKIES


def _get_request_header(request):
    return request.headers


def _get_request_body(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        raise BadRequest({'message': '不是一个JSON'})
    if not isinstance(data, dict):
        raise BadRequest({'message': '不是一个JSON对象'})
    return data
