import inspect
import itertools
import typing

from django.http import HttpRequest

from ._parameters import _Parameters, Body
from .. import spec
from ..http.exceptions import BadRequest
from ..schema.exceptions import DeserializationError
from ..schema.schemas import Schema


class ParameterParser:
    def __init__(self, function):
        self._parameters: typing.Dict[str, _Parameters] = {}
        self._body: typing.Dict[str, Body] = {}

        for name, parameter in inspect.signature(function).parameters.items():
            param = parameter.default

            if isinstance(param, _Parameters):
                self._parameters[name] = param

            elif isinstance(param, Body):
                if self._body:
                    raise ValueError('Cannot have more than one %s.' % type(self._body).__name__)
                self._body[name] = param

    def get_spec_parameters(self):
        params = []
        for param_name, param in self._parameters.items():
            # noinspection PyProtectedMember
            for field_name, field in param.schema._fields.items():
                field: Schema
                params.append({
                    'name': field.alias or field_name,
                    'in': param.location,
                    'required': spec.default_as_none(field.required, False),
                    'description': field.description,
                    'schema': field.to_spec()
                })
        return params

    def get_spec_request_body(self, spec_id=None):
        if not self._body:
            return

        body = list(self._body.values())[0]
        return body.to_spec(spec_id)

    def parse_request(self, request: HttpRequest):
        rv = {}
        for name, param in itertools.chain(self._parameters.items(), self._body.items()):
            try:
                rv[name] = param.parse_request(request)
            except DeserializationError as exc:
                raise BadRequest(exc.error)
        return rv
