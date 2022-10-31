from .types import BaseSchema
from django_openapi.schema.exceptions import ValidationError
from django_openapi.utils.functional import make_schema, Getter


class Discriminator:
    def __init__(self, property_name: str, mapping: dict):
        self.property_name = property_name
        self.mapping = {k: make_schema(v) for k, v in mapping.items()}

    def __get_schema(self, value) -> BaseSchema:
        getter = Getter(value)
        try:
            prop_value = getter(self.property_name)
        except getter.EXCEPTIONS:
            raise ValidationError(f'{self.property_name!r} is required.')

        try:
            return self.mapping[prop_value]
        except (KeyError, TypeError):
            raise ValidationError(f'{self.property_name}={prop_value!r} dose not match the discriminator mapping.')

    def serialize(self, value):
        return self.__get_schema(value).serialize(value)

    def deserialize(self, value):
        return self.__get_schema(value).deserialize(value)


class MixedBase(BaseSchema):
    class Meta:
        data_type = None

    def __init__(self, schema, *schemas, discriminator: Discriminator = None, **kwargs):
        self.schemas = [make_schema(s) for s in [schema, *schemas]]
        self.discriminator = discriminator
        super().__init__(**kwargs)

    def _serialize(self, value):
        if self.discriminator:
            return self.discriminator.serialize(value)

        exc = None
        for schema in self.schemas:
            try:
                return schema.serialize(value)
            except Exception as e:
                exc = e
        raise exc

    def _deserialize(self, value):
        if self.discriminator:
            return self.discriminator.deserialize(value)
        return self._mixed_deserialize(value)

    def _mixed_deserialize(self, value):
        raise NotImplementedError


class OneOf(MixedBase):

    def _mixed_deserialize(self, value):
        # OneOf 只能匹配一个
        rv = empty = object()
        for schema in self.schemas:
            try:
                _rv = schema.deserialize(value)
            except ValidationError:
                continue

            if rv is empty:
                rv = _rv
            else:
                raise ValidationError('multiple schemas were matched.')

        if rv is empty:
            raise ValidationError('no schema is matched.')
        return rv

    def to_spec(self, *args, **kwargs) -> dict:
        spec = super().to_spec(*args, **kwargs)
        spec.update(oneOf=[s.to_spec(*args, **kwargs) for s in self.schemas])
        return spec


class AnyOf(MixedBase):
    def _mixed_deserialize(self, value):
        for schema in self.schemas:
            try:
                return schema.deserialize(value)
            except ValidationError:
                continue
        raise ValidationError('no schema is matched.')

    def to_spec(self, *args, **kwargs) -> dict:
        spec = super().to_spec(*args, **kwargs)
        spec.update(anyOf=[s.to_spec(*args, **kwargs) for s in self.schemas])
        return spec
