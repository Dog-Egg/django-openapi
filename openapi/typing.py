import typing

from openapi.schemax.fields import Schema, Field

GeneralSchemaType = typing.Union[
    Schema,
    typing.Union[Schema],
    typing.Dict[str, Field]
]
