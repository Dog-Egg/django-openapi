import typing

from openapi.schema.schemas import Model, SchemaABC

GeneralModelSchema = typing.Union[
    Model,
    typing.Type[Model],
    typing.Dict[str, SchemaABC]
]

GeneralSchema = typing.Union[
    SchemaABC,
    typing.Type[SchemaABC],
    GeneralModelSchema,
]
