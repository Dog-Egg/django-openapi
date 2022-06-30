import datetime
import operator
import typing
from collections import defaultdict
from collections.abc import Mapping

from openapi.schemax.validators import Validator
from openapi.schemax.exceptions import ValidationError
from openapi.spec.schema import SchemaObject, ReferenceObject
from openapi.spec import register
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
            fallback: typing.Callable[[Exception], typing.Any] = None,  # only serialize

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
        self.fallback = fallback

        self.description = description
        self.example = example

    def deserialize(self, obj):
        obj = self._deserialize(obj)
        errors = []

        for validator in self.validators:
            try:
                validator.validate(obj)
            except ValidationError as exc:
                errors.append(exc.message)

        if errors:
            raise ValidationError(errors)
        return obj

    def _deserialize(self, obj):
        raise NotImplementedError

    def serialize(self, obj):
        return self._serialize(obj)

    def _serialize(self, obj):
        raise NotImplementedError

    def to_spec(self, *args, **kwargs) -> SchemaObject:
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

    def __getattr__(self, name):
        if name in self._fields:
            return self._fields[name]
        return super().__getattribute__(name)


class Schema(Field, _ContainerField, metaclass=_SchemaMeta):
    _anonymous = False
    _type = 'object'

    def _deserialize(self, obj):
        data = {}
        errors = defaultdict(list)

        for field in self._fields.values():
            if field.key not in obj:
                # required
                if field.required:
                    errors[field.key].append('这个字段是必需的')

                # default
                if field.default is not undefined:
                    data[field.name] = field.default
                elif field.default_factory is not None:
                    data[field.name] = field.default_factory()

                continue

            try:
                data[field.name] = field.deserialize(obj[field.key])
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
        return data

    def _serialize(self, obj):
        get_value = operator.getitem if isinstance(obj, Mapping) else getattr
        values = {}
        for field in self._fields.values():
            try:
                value = get_value(obj, field.name)
            except (AttributeError, KeyError):
                if field.required:
                    raise
            else:
                values[field.key] = field.serialize(value)
        return values

    @classmethod
    def from_dict(cls, fields: typing.Dict[str, Field], *, name: str = None):
        # noinspection PyTypeChecker
        schema_cls: typing.Type['Schema'] = type(name or 'AnonymousSchema', (cls,), fields)
        if name is None:
            schema_cls._anonymous = True
        return schema_cls

    @classmethod
    def clone(cls, *, include: typing.Iterable[str] = None, exclude: typing.Iterable[str] = None, name: str = None):
        if include and exclude:
            raise ValueError('不能同时定义 include 和 exclude')
        fields = {}
        for field in cls._fields.values():
            if (not include and not exclude) or (
                    include and field.name in include) or (
                    exclude and field.name not in exclude):
                fields[field.name] = field
        return cls.from_dict(fields, name=name)

    def to_spec(self, spec_id) -> typing.Union[SchemaObject, ReferenceObject]:
        obj = super().to_spec()
        properties = {}
        required = []
        for field in self._fields.values():
            properties[field.key] = field.to_spec(spec_id)
            if field.required:
                required.append(field.key)
        obj.extra(properties=properties, required=required, description=self.__class__.__doc__)
        if not self._anonymous:
            schema_name = self.__class__.__name__
            register.components.register_schema(spec_id, name=schema_name, schema=obj)
            return ReferenceObject(ref='#/components/schemas/%s' % schema_name)
        return obj


class String(Field):
    _type = 'string'

    def __init__(self, *args, strip=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.strip = strip

    def _deserialize(self, obj):
        string = str(obj)
        if self.strip:
            string = string.strip()
        return string

    def _serialize(self, obj):
        return str(obj)


class Integer(Field):
    _type = 'integer'

    def _deserialize(self, obj):
        try:
            return int(obj)
        except ValueError:
            raise ValidationError('不是一个整数')

    def _serialize(self, obj):
        return int(obj)


class List(Field, _ContainerField):
    _type = 'array'

    def __init__(self, field_or_cls: typing.Union[Field, typing.Type[Field]], *args, **kwargs):
        self._field: Field = make_instance(field_or_cls)
        super().__init__(*args, **kwargs)

    def _deserialize(self, obj):
        rv = []
        errors = defaultdict(list)

        for index, item in enumerate(obj):
            try:
                rv.append(self._field.deserialize(item))
            except ValidationError as exc:
                errors[index].append(exc.message)

        if errors:
            raise ValidationError(dict(errors))
        return rv

    def _serialize(self, obj):
        rv = []
        for item in obj:
            rv.append(self._field.serialize(item))
        return rv

    def to_spec(self, spec_id) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(items=self._field.to_spec(spec_id))
        return obj


class Datetime(Field):
    _type = 'string'

    def _deserialize(self, obj):
        pass

    def _serialize(self, obj: datetime.datetime):
        return obj.isoformat()

    def to_spec(self, *args, **kwargs) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(format='date-time')
        return obj


class Date(Field):
    _type = 'string'

    def _deserialize(self, date_string):
        return datetime.date.fromisoformat(date_string)

    def _serialize(self, date: datetime.date):
        return date.isoformat()

    def to_spec(self, *args, **kwargs) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(format='date')
        return obj
