import typing

from django.http.response import HttpResponseBase

from django_openapi import spec
from django_openapi.schema.schemas import Model, BaseSchema

GeneralModelSchema = typing.Union[
    Model,
    typing.Type[Model],
    typing.Dict[str, BaseSchema]
]

GeneralSchema = typing.Union[
    BaseSchema,
    typing.Type[BaseSchema],
    GeneralModelSchema,
]

ErrorHandler = typing.Callable[[Exception], HttpResponseBase]
ErrorHandlers = typing.Dict[typing.Type[Exception], ErrorHandler]

Tags = typing.List[typing.Union[str, spec.Tag]]
