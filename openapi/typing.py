import typing

from openapi.schema.schemas import Model, Schema

GeneralModelSchema = typing.Union[
    Model,
    typing.Type[Model],
    typing.Dict[str, Schema]
]

GeneralSchema = typing.Union[
    Schema,
    typing.Type[Schema],
    GeneralModelSchema,
]
