from marshmallow import fields, missing, Schema as _Schema

from openapi.spec.schema import SchemaObject, ParameterObject


class Parameter:
    type = None

    def __init__(
            self,
            /,
            name=None,
            in_=None,
            default=missing,
            description: str = None,
            example=None,
    ):
        self.in_ = in_
        self.default = default
        self.required = default is missing
        self.description = description
        self.name = name
        self.example = example

    def build_marshmallow_field(self):
        raise NotImplementedError

    def to_spec(self):
        return ParameterObject(
            name=self.name,
            in_=self.in_ or ParameterObject.InEnum.QUERY,
            required=self.required,
            description=self.description,
            schema=SchemaObject(
                type=self.type,
                default=None if self.default is missing else self.default,
            ),
            example=self.example,
        )

    @property
    def _marshmallow_field_kwargs(self):
        return dict(
            missing=self.default,
            data_key=self.name,
            required=self.required,
        )


class StringParameter(Parameter):
    type = SchemaObject.TypeEnum.STRING

    def build_marshmallow_field(self):
        return fields.String(**self._marshmallow_field_kwargs)


class IntegerParameter(Parameter):
    type = SchemaObject.TypeEnum.INTEGER

    def build_marshmallow_field(self):
        return fields.Integer(**self._marshmallow_field_kwargs)


Schema = _Schema
