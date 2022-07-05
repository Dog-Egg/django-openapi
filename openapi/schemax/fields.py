import datetime
import operator
import typing
from collections import defaultdict
from collections.abc import Mapping, Iterable

from openapi.enums import JsonSchemaType, JsonSchemaFormat
from openapi.schemax.validators import Validator, Choices
from openapi.schemax.exceptions import DeserializationError, SerializationError
from openapi.spec.schema import SchemaObject, ReferenceObject, ComponentsObject
from openapi.utils import make_instance

undefined = type('undefined', (), {'__bool__': lambda self: False})()


class Field:
    _type = None

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.__kwargs = kwargs
        self.__args = args
        return self

    def __init__(
            self,
            *,
            key: str = None,
            attr: str = None,
            required: bool = None,  # apply to schema
            nullable: bool = False,
            default=undefined,  # only deserialize
            validators: typing.List[Validator] = None,  # only deserialize
            fallback: typing.Callable[[Exception], typing.Any] = None,  # only serialize
            serialize_only=False,
            choices=None,

            description: str = None,  # openapi spec
            example=None  # openapi spec
    ):
        self.key = key  # serialize: attr -> key
        self.attr = attr  # deserialize: key -> attr
        self.name = None  # field name
        self.required = required if isinstance(required, bool) else (default is undefined)
        self.nullable = nullable
        self.default = default
        self.validators = validators or []
        self.fallback = fallback
        self.serialize_only = serialize_only

        self.description = description
        self.example = example

        # enum
        self.choices = choices
        if choices:
            self.validators.append(Choices(choices))

    def deserialize(self, obj):
        if obj is None:
            if self.nullable:
                return obj
            else:
                raise DeserializationError('不能为 None')

        obj = self._deserialize(obj)
        errors = []
        for validator in self.validators:
            try:
                validator.validate(obj)
            except DeserializationError as exc:
                errors.append(exc.message)

        if errors:
            raise DeserializationError(errors)
        return obj

    def _deserialize(self, obj):
        raise NotImplementedError

    def serialize(self, obj):
        if obj is None:
            if self.nullable:
                return obj
            else:
                raise SerializationError('不能为 null')
        return self._serialize(obj)

    def _serialize(self, obj):
        raise NotImplementedError

    def copy_with(self, **kwargs):
        _args = self.__args
        _kwargs = self.__kwargs.copy()
        _kwargs.update(**kwargs)
        return self.__class__(*_args, **_kwargs)

    def to_spec(self, *args, **kwargs) -> SchemaObject:
        return SchemaObject(
            type=self._type,
            default=self.default or None,
            example=self.example,
            description=self.description,
            read_only=self.serialize_only,
            enum=self.choices,
            nullable=self.nullable,
        )


class _ContainerField:
    pass


class _SchemaMeta(type):
    _fields: typing.Dict[str, Field]

    def __new__(mcs, classname, bases, attrs: dict):
        fields = {}

        # inherit fields
        for base in bases[::-1]:
            if isinstance(base, _SchemaMeta):
                fields.update(base._fields)

        for name, field in attrs.copy().items():
            if isinstance(field, Field):
                field.name = name
                if field.key is None:
                    field.key = name
                if field.attr is None:
                    field.attr = name
                fields[name] = field
                del attrs[name]

        cls = super().__new__(mcs, classname, bases, attrs)
        cls._fields = fields
        return cls

    def __getattr__(self, name):
        # Schema.field      # ok
        # Schema().field    # error
        if name in self._fields:
            return self._fields[name]
        return super().__getattribute__(name)


class Schema(Field, _ContainerField, metaclass=_SchemaMeta):
    _anonymous = False
    _type = JsonSchemaType.OBJECT

    def __init__(self, *args, required_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__required_fields = required_fields

    def __is_required(self, field: Field):
        if self.__required_fields is not None:
            return field.name in self.__required_fields
        return field.required

    def _deserialize(self, obj):
        data = {}
        errors = defaultdict(list)

        for field in self._fields.values():
            if field.serialize_only:
                continue

            if field.key not in obj:
                # required
                if self.__is_required(field):
                    errors[field.key].append('这个字段是必需的')

                # default
                if field.default is not undefined:
                    data[field.attr] = field.default

                continue

            try:
                data[field.attr] = field.deserialize(obj[field.key])
            except DeserializationError as exc:
                key = field.key
                if isinstance(field, _ContainerField):
                    errors[key] = exc.message
                else:
                    if isinstance(exc.message, list):
                        errors[key].extend(exc.message)
                    else:
                        errors[key].append(exc.message)

        if errors:
            raise DeserializationError(dict(errors))
        return data

    def _serialize(self, obj):
        get_value = operator.getitem if isinstance(obj, Mapping) else getattr
        values = {}
        for field in self._fields.values():
            try:
                value = get_value(obj, field.attr)
            except (AttributeError, KeyError):
                if self.__is_required(field):
                    raise
            else:
                values[field.key] = field.serialize(value)
        return values

    @classmethod
    def from_dict(cls, fields: typing.Dict[str, Field], *, name: str = None):
        # noinspection PyTypeChecker
        schema_cls: typing.Type['Schema'] = type(name or 'AnonymousSchema', (Schema,), fields)
        if name is None:
            schema_cls._anonymous = True
        return schema_cls

    # @classmethod
    # def partial(cls, *, include: typing.Iterable[str] = None, exclude: typing.Iterable[str] = None, name: str = None):
    #     if include and exclude:
    #         raise ValueError('不能同时定义 include 和 exclude')
    #     fields = {}
    #     for field in cls._fields.values():
    #         if (not include and not exclude) or (
    #                 include and field.name in include) or (
    #                 exclude and field.name not in exclude):
    #             fields[field.name] = field
    #     return cls.from_dict(fields, name=name)

    def to_spec(self, spec_id) -> typing.Union[SchemaObject, ReferenceObject]:
        obj = super().to_spec()
        properties = {}
        required = []
        for field in self._fields.values():
            properties[field.key] = field.to_spec(spec_id)
            if self.__is_required(field):
                required.append(field.key)

        # required 不添加到 component schemas
        obj.extra(properties=properties, required=required, description=self.__class__.__doc__)

        if not self._anonymous:
            # 非匿名 Schema 使用 openapi components 进行复用
            schema_name = self.__class__.__name__

            # 注册的 Schema 不直接添加 required
            # 清除 required
            obj.extra(required=[])

            # 注册到 openapi components
            ComponentsObject.register(spec_id=spec_id, component_name='schemas', key=schema_name, value=obj)

            # 返回 Schema 引用
            ref = ReferenceObject(ref='#/components/schemas/%s' % schema_name)
            if required:
                # required 利用 allOf 组合
                return SchemaObject(allOf=[ref, {'required': required}])
            return ref

        return obj


class String(Field):
    _type = JsonSchemaType.STRING

    def __init__(self, *args, strip=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.strip = strip  # only deserialize

    def _deserialize(self, value):
        if not isinstance(value, str):
            raise DeserializationError('必须是字符串')

        if self.strip:
            value = value.strip()
        return value

    def _serialize(self, value):
        if not isinstance(value, str):
            raise SerializationError('必须是字符串')

        return value


class Integer(Field):
    _type = JsonSchemaType.INTEGER

    def _deserialize(self, value):
        try:
            f = float(value)
        except (ValueError, TypeError):
            raise DeserializationError('不是一个整数')

        i = int(f)
        if i != f:
            raise DeserializationError('不是一个整数')
        return i

    def _serialize(self, value):
        if not isinstance(value, int):
            raise SerializationError('不是一个整数')
        return value


class Float(Field):
    _type = JsonSchemaType.NUMBER

    def _deserialize(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            raise DeserializationError('不是一个浮点数')

    def _serialize(self, value):
        if not isinstance(value, float):
            raise SerializationError('不是一个浮点数')
        return value

    def to_spec(self, *args, **kwargs) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(format=JsonSchemaFormat.FLOAT)
        return obj


class Boolean(Field):
    _type = JsonSchemaType.BOOLEAN
    TRUE_VALUES = {1, '1', 'true', 'True', True}
    FALSE_VALUES = {0, '0', 'false', 'False', False}

    def _deserialize(self, obj):
        if obj in self.TRUE_VALUES:
            return True
        if obj in self.FALSE_VALUES:
            return False
        raise DeserializationError('不是一个有效布尔值')

    def _serialize(self, obj):
        if not isinstance(obj, bool):
            raise SerializationError('不是一个有效布尔值')
        return obj


class List(Field, _ContainerField):
    _type = JsonSchemaType.ARRAY

    def __init__(self, field_or_cls: typing.Union[Field, typing.Type[Field]] = None, *args, **kwargs):
        self._field: Field = make_instance(field_or_cls) or Any()
        super().__init__(*args, **kwargs)

    def _deserialize(self, obj):
        if not isinstance(obj, Iterable):
            raise DeserializationError('不是一个可迭代对象')

        rv = []
        errors = defaultdict(list)

        for index, item in enumerate(obj):
            try:
                rv.append(self._field.deserialize(item))
            except DeserializationError as exc:
                errors[index].append(exc.message)

        if errors:
            raise DeserializationError(dict(errors))
        return rv

    def _serialize(self, obj):
        if not isinstance(obj, Iterable):
            raise SerializationError('不是一个可迭代对象')

        rv = []
        for item in obj:
            rv.append(self._field.serialize(item))
        return rv

    def to_spec(self, spec_id) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(items=self._field.to_spec(spec_id))
        return obj


class Datetime(Field):
    _type = JsonSchemaType.STRING

    def _deserialize(self, obj):
        pass

    def _serialize(self, obj: datetime.datetime):
        return obj.isoformat()

    def to_spec(self, *args, **kwargs) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(format=JsonSchemaFormat.DATETIME)
        return obj


class Date(Field):
    _type = JsonSchemaType.STRING

    def _deserialize(self, date_string):
        if not isinstance(date_string, str):
            raise DeserializationError('不是一个有效的日期值')
        try:
            return datetime.date.fromisoformat(date_string)
        except ValueError:
            raise DeserializationError('不是一个有效的日期值')

    def _serialize(self, date: datetime.date):
        if not isinstance(date, datetime.date):
            raise SerializationError('不是一个日期对象')
        return date.isoformat()

    def to_spec(self, *args, **kwargs) -> SchemaObject:
        obj = super().to_spec()
        obj.extra(format=JsonSchemaFormat.DATE)
        return obj


class Any(Field):
    # TODO nullable? _type? enum?
    def _deserialize(self, obj):
        return obj

    def _serialize(self, obj):
        return obj
