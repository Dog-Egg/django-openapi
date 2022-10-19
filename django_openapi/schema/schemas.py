import datetime
import hashlib
import inspect
import itertools
import operator
import typing
from collections.abc import Mapping, Iterable

from dateutil.parser import isoparse

from django_openapi.parameters.style import Style
from django_openapi.schema import validators as _validators
from django_openapi.schema.exceptions import ValidationError
from django_openapi.utils.functional import Filter, make_schema, make_instance
from django_openapi.spec import utils as _spec

UNDEFINED = type('undefined', (), {})()

_INHERITABLE_METADATA: dict = dict(
    data_type='string',
    data_format=None,
    default_validators=[],
)
_NON_INHERITED_METADATA = dict(
    register_as_component=True,
    schema_name=None,
)


class _SchemaMeta(type):
    def __new__(mcs, name, bases, attrs):
        parents = [base for base in bases if isinstance(base, _SchemaMeta)]
        if not parents:
            return super().__new__(mcs, name, bases, attrs)

        for parent in parents:
            if hasattr(parent, '_metadata'):
                metadata = getattr(parent, '_metadata').copy()
                break
        else:
            metadata = _INHERITABLE_METADATA.copy()
        metadata.update(_NON_INHERITED_METADATA)  # 重置不会继承的 metadata

        Meta = attrs.get('Meta')  # 自定义修改
        if inspect.isclass(Meta):
            for key in itertools.chain(_INHERITABLE_METADATA, _NON_INHERITED_METADATA):
                if hasattr(Meta, key):
                    metadata[key] = getattr(Meta, key)

        attrs['_metadata'] = metadata
        return super().__new__(mcs, name, bases, attrs)


class BaseSchema(metaclass=_SchemaMeta):
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
            default=UNDEFINED,  # only deserialize
            serialize_preprocess: typing.Callable[[typing.Any], typing.Any] = None,
            validators: typing.List[typing.Callable[[typing.Any], None]] = None,  # only deserialize
            fallback: typing.Callable[[typing.Any], typing.Any] = None,  # only serialize
            read_only=False,
            write_only=False,
            allow_blank=False,  # only deserialize
            choices=None,
            description: str = None,  # openapi spec
            example=None,  # openapi spec
            style: Style = None,
    ):
        self.alias = alias  # serialize: attr -> alias
        self.attr = attr  # deserialize: alias -> attr
        self.name = None  # field name
        self.required = required if isinstance(required, bool) else (default is UNDEFINED)  # 仅反序列使用
        self.nullable = nullable
        self.default = default
        self.serialize_preprocess = serialize_preprocess
        self._validators: typing.List[typing.Callable[[typing.Any], None]] = validators or []
        self.fallback = fallback
        self.read_only = read_only
        self.write_only = write_only
        self.allow_blank = allow_blank

        self.description = _spec.clean_commonmark(description)
        self.example = example

        self.style = style or Style()
        self.style.schema = self

        # enum
        self.choices = choices
        if choices:
            self._validators.append(_validators.ChoicesValidator(choices))

    def deserialize(self, obj):
        if obj is None:
            if self.nullable:
                return obj
            else:
                raise ValidationError('The value cannot be null')

        obj = self._deserialize(obj)
        error = ValidationError()
        for validator in itertools.chain(self._metadata['default_validators'], self._validators):
            try:
                validator(obj)
            except ValidationError as exc:
                error.concat(exc)

        if error.nonempty:
            raise error
        return obj

    def _deserialize(self, obj):
        raise NotImplementedError

    def serialize(self, obj):
        try:
            if obj is None:
                if self.nullable:
                    return obj
                raise ValueError('The value cannot be None')
            if self.serialize_preprocess:
                obj = self.serialize_preprocess(obj)
            return self._serialize(obj)
        except Exception:
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

    def to_spec(self, *args, **kwargs) -> dict:
        return dict(
            type=self._metadata['data_type'],
            default=None if self.default is UNDEFINED else self.default,
            example=self.example,
            description=self.description,
            readOnly=_spec.default_as_none(self.read_only, False),
            writeOnly=_spec.default_as_none(self.write_only, False),
            enum=self.choices,
            nullable=_spec.default_as_none(self.nullable, False),
            format=self._metadata['data_format']
        )


class _ModelFields:
    def __init__(self, fields: typing.Dict[str, BaseSchema]):
        self.__fields = fields

    def __getattr__(self, name):
        if name in self.__fields:
            return self.__fields[name]
        return super().__getattribute__(name)

    def __iter__(self):
        return iter(self.__fields.values())

    def __len__(self):
        return len(self.__fields)


class _ModelMeta(_SchemaMeta):
    fields: _ModelFields

    def __new__(mcs, classname, bases, attrs: dict):
        fields = {}

        # inherit fields
        for base in bases[::-1]:
            if isinstance(base, _ModelMeta):
                for field in base.fields:
                    fields[field.name] = field

        for name, field in attrs.copy().items():
            if isinstance(field, BaseSchema):
                field.name = name
                if field.alias is None:
                    field.alias = name
                if field.attr is None:
                    field.attr = name
                fields[name] = field
                del attrs[name]
            attrs['fields'] = _ModelFields(fields)
        return super().__new__(mcs, classname, bases, attrs)


class Model(BaseSchema, metaclass=_ModelMeta):
    fields: _ModelFields

    class Meta:
        data_type = 'object'

    def __init__(self,
                 *args,
                 required_fields=None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.__required_fields = required_fields

    def __check_required(self, field: BaseSchema):
        if self.__required_fields == '__all__':
            return True

        if self.__required_fields is not None:
            return field.name in self.__required_fields
        return field.required

    def _deserialize(self, obj: dict):
        data = {}
        error = ValidationError()

        for field in self.fields:
            if field.read_only:
                continue

            if (
                    field.alias not in obj
            ) or (
                    not field.allow_blank and obj[field.alias] == ''
            ):
                # required
                if self.__check_required(field):
                    msg = '字段不能为空' if field.alias in obj else '这个字段是必需的'
                    error.setitem(field.alias, ValidationError(msg))

                # default
                if field.default is not UNDEFINED:
                    data[field.attr] = field.default

                continue

            try:
                data[field.attr] = field.deserialize(obj[field.alias])
            except ValidationError as exc:
                error.setitem(field.alias, exc)

        if error.nonempty:
            raise error
        return data

    def _serialize(self, obj):
        get_value = operator.getitem if isinstance(obj, Mapping) else getattr
        values = {}
        for field in self.fields:
            field: BaseSchema
            if field.write_only:
                continue
            try:
                value = get_value(obj, field.attr)
            except (AttributeError, KeyError):
                if field.fallback:
                    # Model 字段 fallback 返回的值，仍需要去被字段序列
                    value = field.fallback(UNDEFINED)
                else:
                    raise

            try:
                values[field.alias] = field.serialize(value)
            except Exception as e:
                raise type(e)('%s field %r: %s' % (self, field.attr, e)).with_traceback(e.__traceback__)
        return values

    @classmethod
    def from_dict(cls, fields: typing.Dict[str, BaseSchema]) -> typing.Type['Model']:
        attrs: dict = dict(fields)

        class Meta:
            register_as_component = False

        attrs.setdefault('Meta', Meta)
        return typing.cast(typing.Type[Model], type('GeneratedSchema', (Model,), attrs))

    @classmethod
    def partial(
            cls, *,
            include_fields: typing.Iterable[str] = None,
            exclude_fields: typing.Iterable[str] = None,
    ):
        filter_ = Filter(include_fields, exclude_fields)
        fields = {}
        for field in cls.fields:
            if filter_.check(field.name):
                fields[field.name] = field
        return cls.from_dict(fields)

    def __get_required_list(self):
        required = []
        for field in self.fields:
            if self.__check_required(field):
                required.append(field.alias)
        return required

    def to_spec(self, spec_id, *, need_required_field=False, schema_id=None):
        spec = super().to_spec()
        properties = {}
        for field in self.fields:
            field: BaseSchema
            properties[field.alias] = field.to_spec(spec_id)

        __doc__ = _spec.clean_commonmark(self.__class__.__doc__)

        spec.update(
            properties=properties,
            required=self.__get_required_list() if need_required_field else None,
            description=self.description or __doc__  # 没有被注册为组件优先使用 description
        )

        if schema_id or self._metadata['register_as_component']:
            spec.update(
                title=self._metadata['schema_name'] or self.__class__.__name__,
                description=__doc__  # 注册为组件只使用 __doc__，因为 description 是动态的
            )

            # 需要去使用复合的字段
            composite = _spec.clean({k: spec[k] for k in ['required', 'nullable']})

            if not schema_id:
                schema_id = '%s.%s' % (self.__class__.__module__, self.__class__.__qualname__)
                parts = schema_id.rsplit('.', 1)
                parts[0] = hashlib.md5(parts[0].encode()).hexdigest()[:8]
                schema_id = '.'.join(parts)

                # 没有提供 schema_id 在注册到 components 之前清除复合字段
                composite and [spec.pop(k) for k in composite]

            # 注册到 openapi components
            _spec.Collection(spec_id).schemas[schema_id] = spec

            # 返回 Schema 引用
            ref = {'$ref': '#/components/schemas/%s' % schema_id}
            if composite:
                # 利用 allOf 组合
                return dict(allOf=[ref, composite])
            return ref

        return spec


class String(BaseSchema):
    class Meta:
        data_type = 'string'

    def __init__(self, *args, strip=False, min_length=None, max_length=None, pattern=None, whitespace: bool = None,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self.strip = strip  # only deserialize

        # 绝大多数时候不希望收到一个空白的字符串，whitespace 默认值应该为 False
        # 但 whitespace 需要先兼容 allow_blank
        self.whitespace = self.allow_blank if whitespace is None else whitespace  # only deserialize

        self.min_length = min_length
        self.max_length = max_length
        if min_length is not None or max_length is not None:
            self._validators.append(_validators.LengthValidator(min_length=min_length, max_length=max_length))

        self.pattern = pattern
        if pattern:
            regexp = _validators.RegExpValidator(pattern)
            self.pattern = regexp.pattern.pattern
            self._validators.append(regexp)

    def _deserialize(self, value):
        if not isinstance(value, str):
            raise ValidationError('必须是字符串')

        if self.strip:
            value = value.strip()

        if not self.whitespace and (not value or not value.strip()):
            raise ValidationError('cannot be a whitespace string')

        return value

    def _serialize(self, value):
        return str(value)

    def to_spec(self, *args, **kwargs):
        spec = super().to_spec(*args, **kwargs)
        spec.update(
            maxLength=self.max_length,
            minLength=self.min_length,
            pattern=self.pattern,
        )
        return spec


class _Number(BaseSchema):
    def __init__(self, *args, gt=None, gte=None, lt=None, lte=None, multiple_of=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte
        if any(x is not None for x in (gt, gte, lt, lte)):
            self._validators.append(_validators.RangeValidator(gt=gt, gte=gte, lt=lt, lte=lte))

        self.multiple_of = multiple_of
        if multiple_of is not None:
            self._validators.append(_validators.MultipleOfValidator(self.multiple_of))

    def _deserialize(self, obj):
        raise NotImplementedError

    def _serialize(self, obj):
        raise NotImplementedError

    def to_spec(self, *args, **kwargs):
        spec = super().to_spec(*args, **kwargs)
        spec.update(
            maximum=self.lte if self.lt is None else self.lt,
            exclusiveMaximum=self.lt is not None or None,
            minimum=self.gte if self.gt is None else self.gt,
            exclusiveMinimum=self.gt is not None or None,
            multipleOf=self.multiple_of,
        )
        return spec


class Integer(_Number):
    class Meta:
        data_type = 'integer'

    def _deserialize(self, value):
        try:
            f = float(value)
        except (ValueError, TypeError):
            raise ValidationError('不是一个整数')

        i = int(f)
        if i != f:
            raise ValidationError('不是一个整数')
        return i

    def _serialize(self, value):
        return int(value)


class Float(_Number):
    class Meta:
        data_type = 'number'
        data_format = 'float'

    def _deserialize(self, value):
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValidationError('不是一个浮点数')

    def _serialize(self, value):
        return float(value)


class Boolean(BaseSchema):
    TRUE_VALUES = {1, '1', 'true', 'True', True}
    FALSE_VALUES = {0, '0', 'false', 'False', False}

    class Meta:
        data_type = 'boolean'

    def _deserialize(self, obj):
        if obj in self.TRUE_VALUES:
            return True
        if obj in self.FALSE_VALUES:
            return False
        raise ValidationError('不是一个有效布尔值')

    def _serialize(self, obj):
        return bool(obj)


class List(BaseSchema):
    class Meta:
        data_type = 'array'

    def __init__(
            self,
            child=None,
            *args,
            max_items: typing.Optional[int] = None,
            min_items: typing.Optional[int] = None,
            unique_items: bool = False,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._child: BaseSchema = make_schema(child or Any())
        self.max_items = max_items
        self.min_items = min_items
        self.unique_items: bool = unique_items

        if self.max_items or self.min_items:
            self._validators.append(_validators.LengthValidator(min_length=self.min_items, max_length=self.max_items))
        if self.unique_items:
            self._validators.append(_validators.unique_validate)

    def _deserialize(self, obj):
        if not isinstance(obj, Iterable):
            raise ValidationError('不是一个可迭代对象')

        rv = []
        error = ValidationError()

        for index, item in enumerate(obj):
            try:
                rv.append(self._child.deserialize(item))
            except ValidationError as exc:
                error.setitem(index, exc)

        if error.nonempty:
            raise error
        return rv

    def _serialize(self, obj):
        rv = []
        for item in obj:
            rv.append(self._child.serialize(item))
        return rv

    def to_spec(self, spec_id=None):
        spec = super().to_spec()
        spec.update(
            items=self._child.to_spec(spec_id),
            maxItems=self.max_items,
            minItems=self.min_items,
            uniqueItems=_spec.default_as_none(self.unique_items, False),
        )
        return spec


class Dict(BaseSchema):
    class Meta:
        data_type = 'object'

    def __init__(self, value=None, key=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.value_schema = make_instance(value) or Any()
        self.key_schema = make_instance(key) or String()

    def _deserialize(self, obj):
        if not isinstance(obj, dict):
            raise ValidationError('not a valid dict object.')
        rv = {}
        for key, val in obj.items():
            try:
                key = self.key_schema.deserialize(key)
            except ValidationError as e:
                raise ValidationError('The key %s' % e)
            try:
                val = self.value_schema.deserialize(val)
            except ValidationError as e:
                raise ValidationError('The value %s' % e)
            rv[key] = val
        return rv

    def _serialize(self, obj):
        return {self.key_schema.serialize(key): self.value_schema.serialize(val) for key, val in obj.items()}


class Date(BaseSchema):
    def __init__(self, *args, fmt=None, dfmt=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._fmt = fmt
        self._dfmt = dfmt

    class Meta:
        data_type = 'string'
        data_format = 'date'

    def _strptime(self, date_string) -> datetime.datetime:
        if self._dfmt is not None:
            return datetime.datetime.strptime(date_string, self._dfmt)
        return isoparse(date_string)

    def _deserialize(self, date_string) -> datetime.date:
        try:
            return self._strptime(date_string).date()
        except (ValueError, TypeError):
            raise ValidationError('Not a valid date string.')

    def _serialize(self, date: datetime.date):
        if self._fmt is not None:
            return date.strftime(self._fmt)
        return date.isoformat()


class Datetime(Date):
    class Meta:
        data_type = 'string'
        data_format = 'date-time'

    def _deserialize(self, date_string):
        try:
            return self._strptime(date_string)
        except (ValueError, TypeError):
            raise ValidationError('Not a valid datetime string.')


class Any(BaseSchema):
    class Meta:
        data_type = None

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('nullable', True)
        super().__init__(*args, **kwargs)

    def _deserialize(self, obj):
        return obj

    def _serialize(self, obj):
        return obj

    def to_spec(self, *args, **kwargs):
        return _spec.Protect(super().to_spec(*args, **kwargs))


class Password(String):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('write_only', True)
        super().__init__(*args, **kwargs)

    class Meta:
        data_format = 'password'


class File(BaseSchema):
    class Meta:
        data_type = 'string'

    def __init__(self, *args, data_format='binary', **kwargs):
        super().__init__(*args, **kwargs)
        self.data_format = data_format

    def _deserialize(self, obj):
        from django.core.files import File
        if not isinstance(obj, File):
            raise ValidationError('不是一个文件')
        return obj

    def _serialize(self, obj):
        pass

    def to_spec(self, *args, **kwargs):
        spec = super().to_spec(*args, **kwargs)
        spec.update(format=self.data_format)
        return spec


class Path(String):
    pass
