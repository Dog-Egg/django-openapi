import typing
from collections import defaultdict

from openapi.schemax.validators import Validator
from openapi.schemax.exceptions import ValidationError
from openapi.schemax.utils import PureObject
from openapi.spec.schema import SchemaObject, ComponentsObject, ReferenceObject
from openapi.spec.utils import OPENAPI_SCHEMA_CONTAINER
from openapi.utils import make_instance

undefined = type('undefined', (), {'__bool__': lambda self: False})()


class Field:
    _type = None

    def __init__(
            self,
            *,
            key: str = None,
            required: bool = False,  # only deserialize
            default=undefined,  # only deserialize
            default_factory: typing.Callable[[], typing.Any] = None,  # only deserialize
            validators: typing.List[Validator] = None,  # only deserialize

            description: str = None,  # openapi spec
            example=None  # openapi spec
    ):
        if default is not undefined and default_factory is not None:
            raise ValueError('不能同时定义 default 和 default_factory')

        self.key = key
        self.name = None
        self.required = required
        self.default = default
        self.default_factory = default_factory
        self.validators = validators or []

        self.description = description
        self.example = example

    def deserialize(self, value):
        value = self._deserialize(value)
        errors = []

        for validator in self.validators:
            try:
                validator.validate(value)
            except ValidationError as exc:
                errors.append(exc.message)

        if errors:
            raise ValidationError(errors)
        return value

    def _deserialize(self, value):
        raise NotImplementedError

    def to_spec(self) -> SchemaObject:
        return SchemaObject(
            type=self._type,
            default=self.default or None,
            example=self.example,
            description=self.description
        )


class _ContainerField:
    pass


class _SchemaMeta(type):
    def __new__(mcs, classname, bases, attrs):
        fields: typing.Dict[str, Field] = {}
        for name, field in attrs.copy().items():
            if isinstance(field, Field):
                field.name = name
                if field.key is None:
                    field.key = name
                fields[name] = field
                del attrs[name]

        cls = super().__new__(mcs, classname, bases, attrs)
        cls._fields = fields
        return cls


class Schema(Field, _ContainerField, metaclass=_SchemaMeta):
    _named = True
    _type = 'object'

    def _deserialize(self, value):
        kwargs = {}
        errors = defaultdict(list)

        for field in self._fields.values():
            if field.key not in value:
                # required
                if field.required:
                    errors[field.key].append('这个字段是必需的')

                # default
                if field.default is not undefined:
                    kwargs[field.name] = field.default
                elif field.default_factory is not None:
                    kwargs[field.name] = field.default_factory()

                continue

            try:
                kwargs[field.name] = field.deserialize(value[field.key])
            except ValidationError as exc:
                key = field.key
                if isinstance(field, _ContainerField):
                    errors[key] = exc.message
                else:
                    if isinstance(exc.message, list):
                        errors[key].extend(exc.message)
                    else:
                        errors[key].append(exc.message)

        if errors:
            raise ValidationError(dict(errors))
        return PureObject(**kwargs)

    @classmethod
    def from_dict(cls, fields: typing.Dict[str, Field]):
        # noinspection PyTypeChecker
        schema_cls: typing.Type['Schema'] = type('GeneratedSchema', (cls,), fields)
        schema_cls._named = False
        return schema_cls

    @classmethod
    def clone(cls, *, include: typing.Iterable[str] = None, exclude: typing.Iterable[str] = None):
        if include and exclude:
            raise ValueError('不能同时定义 include_fields 和 exclude_fields')
        fields = {}
        for name, field in cls._fields.items():
            if (include and name in include) or (
                    exclude and name not in exclude):
                fields[name] = field
        return cls.from_dict(fields)

    def to_spec(self) -> typing.Union[SchemaObject, ReferenceObject]:
        obj = super().to_spec()
        properties = {}
        required = []
        for field in self._fields.values():
            properties[field.key] = field.to_spec()
            if field.required:
                required.append(field.key)
        obj.extra(properties=properties, required=required)
        if self._named:
            schema_name = self.__class__.__name__
            OPENAPI_SCHEMA_CONTAINER['schemas'][schema_name] = obj
            return ReferenceObject(ref='#/components/schemas/%s' % schema_name)
        return obj


class String(Field):
    _type = 'string'

    def __init__(self, *args, strip=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.strip = strip

    def _deserialize(self, value):
        string = str(value)
        if self.strip:
            string = string.strip()
        return string


class Integer(Field):
    _type = 'integer'

    def _deserialize(self, value):
        try:
            return int(value)
        except ValueError:
            raise ValidationError('不是一个整数')


class List(Field, _ContainerField):
    _type = 'array'

    def __init__(self, field_or_cls: typing.Union[Field, typing.Type[Field]], *args, **kwargs):
        self._field: Field = make_instance(field_or_cls)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value):
        rv = []
        errors = defaultdict(list)

        for index, item in enumerate(value):
            try:
                rv.append(self._field.deserialize(item))
            except ValidationError as exc:
                errors[index].append(exc.message)

        if errors:
            raise ValidationError(dict(errors))
        return rv

    def to_spec(self) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(items=self._field.to_spec())
        return obj
