import typing
from collections import defaultdict

from openapi.schemax.validators import Validator
from openapi.schemax.exceptions import ValidationError
from openapi.schemax.utils import PureObject
from openapi.spec.schema import SchemaObject
from openapi.utils import make_instance

undefined = type('undefined', (), {'__bool__': lambda self: False})()


class Field:
    _type = None

    def __init__(
            self,
            *,
            name: str = None,
            required: bool = False,
            default=undefined,
            default_factory: typing.Callable[[], typing.Any] = None,
            validators: typing.List[Validator] = None,

            location: str = 'query',
            description: str = None,
            example=None
    ):
        if default is not undefined and default_factory is not None:
            raise ValueError('不能同时定义 default 和 default_factory')

        self.name = name
        self.attr = None
        self.required = required
        self.default = default
        self.default_factory = default_factory
        self.validators = validators or []

        self.location = location
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
        fields: typing.List[Field] = []
        for name, field in attrs.copy().items():
            if isinstance(field, Field):
                field.attr = name
                if field.name is None:
                    field.name = name
                fields.append(field)
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

        for field in self._fields:
            if field.name not in value:
                # required
                if field.required:
                    errors[field.name].append('这个字段是必需的')

                # default
                if field.default is not undefined:
                    kwargs[field.attr] = field.default
                elif field.default_factory is not None:
                    kwargs[field.attr] = field.default_factory()

                continue

            try:
                kwargs[field.attr] = field.deserialize(value[field.name])
            except ValidationError as exc:
                field_name = field.name
                if isinstance(field, _ContainerField):
                    errors[field_name] = exc.message
                else:
                    if isinstance(exc.message, list):
                        errors[field_name].extend(exc.message)
                    else:
                        errors[field_name].append(exc.message)

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
    def clone(cls, include_fields: typing.Iterable[str] = None, exclude_fields: typing.Iterable[str] = None):
        if include_fields and exclude_fields:
            raise ValueError('不能同时定义 include_fields 和 exclude_fields')
        fields = {}
        for field in cls._fields:
            if (include_fields and field.attr in include_fields) or (
                    exclude_fields and field.attr not in exclude_fields):
                fields[field.attr] = field
        return cls.from_dict(fields)

    def to_spec(self) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(properties={field.name: field.to_spec() for field in self._fields})
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
