import datetime
import inspect
import operator
import typing
from collections import defaultdict
from collections.abc import Mapping, Iterable

from openapi.enums import DataType, DataFormat
from openapi.schema.validators import Validator, Choices
from openapi.schema.exceptions import DeserializationError, SerializationError
from openapi.spec.schema import SchemaObject, ReferenceObject, ComponentsObject
from openapi.utils import make_instance

undefined = type('undefined', (), {'__bool__': lambda self: False})()

_DEFAULT_METADATA = dict(
    data_type=DataType.STRING,
    data_format=None,
)


class _SchemaMeta(type):

    def __new__(mcs, name, bases, attrs):
        if bases:
            # 继承 metadata
            metadata = getattr(bases[0], '_metadata', _DEFAULT_METADATA).copy()
            meta = attrs.get('Meta')
            if inspect.isclass(meta):
                for key, val in _DEFAULT_METADATA.items():
                    metadata[key] = getattr(meta, key, val)
                del attrs['Meta']
            attrs['_metadata'] = metadata
        return super().__new__(mcs, name, bases, attrs)


class Schema(metaclass=_SchemaMeta):
    _metadata: dict

    def __new__(cls, *args, **kwargs):
        self = super().__new__(cls)
        self.__kwargs = kwargs
        self.__args = args
        return self

    def __init__(
            self,
            *,
            alias: str = None,
            attr: str = None,
            required: bool = None,  # apply to schema
            nullable: bool = False,
            default=undefined,  # only deserialize
            validators: typing.List[Validator] = None,  # only deserialize
            fallback: typing.Callable[[typing.Any], typing.Any] = None,  # only serialize
            serialize_only=False,
            enum=None,

            description: str = None,  # openapi spec
            example=None  # openapi spec
    ):
        self.alias = alias  # serialize: attr -> alias
        self.attr = attr  # deserialize: alias -> attr
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
        self.enum = enum
        if enum:
            self.validators.append(Choices(enum))

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
        try:
            if obj is None:
                if self.nullable:
                    return obj
                else:
                    raise SerializationError('不能为 null')
            return self._serialize(obj)
        except SerializationError:
            if self.fallback:
                return self.fallback(obj)
            raise

    def _serialize(self, obj):
        raise NotImplementedError

    def copy_with(self, **kwargs):
        _args = self.__args
        _kwargs = self.__kwargs.copy()
        _kwargs.update(**kwargs)
        return self.__class__(*_args, **_kwargs)

    def to_spec(self, *args, **kwargs) -> SchemaObject:
        return SchemaObject(
            type=self._metadata['data_type'],
            default=self.default or None,
            example=self.example,
            description=self.description,
            read_only=self.serialize_only,
            enum=self.enum,
            nullable=self.nullable,
            format=self._metadata['data_format']
        )


class _ContainerSchema:
    pass


class _ModelMeta(_SchemaMeta):
    _fields: typing.Dict[str, Schema]

    def __new__(mcs, classname, bases, attrs: dict):
        fields = {}

        # inherit fields
        for base in bases[::-1]:
            if isinstance(base, _ModelMeta):
                fields.update(base._fields)

        for name, field in attrs.copy().items():
            if isinstance(field, Schema):
                if name.startswith('_'):
                    raise ValueError('Field name cannot start with %r' % '_')

                field.name = name
                if field.alias is None:
                    field.alias = name
                if field.attr is None:
                    field.attr = name
                fields[name] = field
                del attrs[name]
            attrs['_fields'] = fields
        return super().__new__(mcs, classname, bases, attrs)

    def __getattr__(self, name):
        # Model.field      # ok
        # Model().field    # error
        if name in self._fields:
            return self._fields[name]
        return super().__getattribute__(name)


class Model(Schema, _ContainerSchema, metaclass=_ModelMeta):
    _anonymous = False

    class Meta:
        data_type = DataType.OBJECT

    def __init__(self, *args, required_fields=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.__required_fields = required_fields

    def __is_required(self, field: Schema):
        if self.__required_fields is not None:
            return field.name in self.__required_fields
        return field.required

    def _deserialize(self, obj):
        data = {}
        errors = defaultdict(list)

        for field in self._fields.values():
            if field.serialize_only:
                continue

            if field.alias not in obj:
                # required
                if self.__is_required(field):
                    errors[field.alias].append('这个字段是必需的')

                # default
                if field.default is not undefined:
                    data[field.attr] = field.default

                continue

            try:
                data[field.attr] = field.deserialize(obj[field.alias])
            except DeserializationError as exc:
                key = field.alias
                if isinstance(field, _ContainerSchema):
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
            field: Schema
            try:
                value = get_value(obj, field.attr)
            except (AttributeError, KeyError):
                if self.__is_required(field):
                    if field.fallback:
                        value = field.fallback(undefined)
                        if value is undefined:
                            continue
                    else:
                        raise SerializationError('%s 不存在 %r' % (obj, field.attr))
                else:
                    continue

            values[field.alias] = field.serialize(value)
        return values

    @classmethod
    def from_dict(cls, fields: typing.Dict[str, Schema], *, name: str = None):
        # noinspection PyTypeChecker
        schema_cls: typing.Type['Model'] = type(name or 'AnonymousSchema', (Model,), fields)
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
            properties[field.alias] = field.to_spec(spec_id)
            if self.__is_required(field):
                required.append(field.alias)

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


class String(Schema):
    class Meta:
        data_type = DataType.STRING

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


class Integer(Schema):
    class Meta:
        data_type = DataType.INTEGER

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


class Float(Schema):
    class Meta:
        data_type = DataType.NUMBER
        data_format = DataFormat.FLOAT

    def _deserialize(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            raise DeserializationError('不是一个浮点数')

    def _serialize(self, value):
        if not isinstance(value, float):
            raise SerializationError('不是一个浮点数')
        return value


class Boolean(Schema):
    TRUE_VALUES = {1, '1', 'true', 'True', True}
    FALSE_VALUES = {0, '0', 'false', 'False', False}

    class Meta:
        data_type = DataType.BOOLEAN

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


class List(Schema, _ContainerSchema):
    class Meta:
        data_type = DataType.ARRAY

    def __init__(self, field_or_cls: typing.Union[Schema, typing.Type[Schema]] = None, *args, **kwargs):
        self._field: Schema = make_instance(field_or_cls) or Any()
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


class Datetime(Schema):
    class Meta:
        data_type = DataType.STRING
        data_format = DataFormat.DATETIME

    def _deserialize(self, obj):
        pass

    def _serialize(self, obj: datetime.datetime):
        return obj.isoformat()


class Date(Schema):
    class Meta:
        data_type = DataType.STRING
        data_format = DataFormat.DATE

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


class Any(Schema):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('nullable', True)
        super().__init__(*args, **kwargs)

    def _deserialize(self, obj):
        return obj

    def _serialize(self, obj):
        return obj


class Password(String):
    class Meta:
        data_format = DataFormat.PASSWORD


class File(Schema):
    class Meta:
        data_type = DataType.STRING

    # noinspection PyShadowingBuiltins
    def __init__(self, *args, data_format=DataFormat.BINARY, **kwargs):
        super().__init__(*args, **kwargs)
        self.data_format = data_format

    def _deserialize(self, obj):
        from django.core.files import File as _File
        if not isinstance(obj, _File):
            raise DeserializationError('不是一个文件')
        return obj

    def _serialize(self, obj):
        return NotImplemented

    def to_spec(self, *args, **kwargs) -> SchemaObject:
        obj = super().to_spec(*args, **kwargs)
        obj.extra(format=self.data_format)
        return obj
