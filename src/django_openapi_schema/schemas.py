import copy
import datetime
import inspect
import re
import typing as t
from collections.abc import Iterable, Mapping

from dateutil.parser import isoparse

from . import _validators
from .constants import EMPTY
from .exceptions import ValidationError
from .spectools.utils import default_as_none
from .utils import make_instance
from .utils.hook import HookClassMeta, get_hook, iter_hooks

__all__ = (
    "Schema",
    "Model",
    "String",
    "Float",
    "Integer",
    "Boolean",
    "Date",
    "Datetime",
    "List",
    "Dict",
    "Any",
    "AnyOf",
    "Password",
)


class MetaOptions(Mapping):
    _inherited_attributes = dict(
        data_type=None,
        data_format=None,
    )
    _exclusive_attributes = dict(
        register_as_component=True,
        schema_name=None,
    )

    def __init__(self, cls: "SchemaMeta"):
        allowed_attrs = {
            *self._inherited_attributes,
            *self._exclusive_attributes,
        }

        opts: t.Dict[str, t.Any]
        for parent in (
            base for base in inspect.getmro(cls)[1:] if isinstance(base, SchemaMeta)
        ):
            if hasattr(parent, "meta"):
                opts = dict(parent.meta)
                break
        else:
            opts = self._inherited_attributes.copy()
        opts.update(self._exclusive_attributes)

        metaclass = getattr(cls, "Meta", None)
        if inspect.isclass(metaclass):
            for attr in dir(metaclass):
                if attr.startswith("_"):
                    continue
                assert attr in allowed_attrs, attr
                opts[attr] = getattr(metaclass, attr, opts[attr])
        self._opts = opts

    def __getitem__(self, item):
        return self._opts[item]

    def __len__(self) -> int:
        return len(self._opts)

    def __iter__(self):
        return iter(self._opts)


class SchemaMeta(HookClassMeta):
    def __init__(cls, classname, bases, attrs: dict, **kwargs):
        super().__init__(classname, bases, attrs, **kwargs)
        cls.meta = MetaOptions(cls)


class Field:
    """定义 `Model <xschema.schemas.Model>` 的字段。这是个抽象类，已被 `Schema` 继承。

    :param required: 设置字段在反序列化时是否为必需。

        如果为 `None`，其值由 ``default`` 参数决定，设置 ``default`` 则这该字段为非必须。

    :param default: 在反序列化时，如果字段为非必须，则可以通过设置该参数来提供默认值。

        可以指定为一个函数，函数返回值将作为默认值使用。

    :param attr: 指定序列化/反序列化时，字段对应的外部数据键。如果为 None，将使用字段名。
    :param alias: 指定序列化/反序列化时，字段对应的内部数据键/属性。如果为 None，将使用字段名。

    :param read_only: 如果为 `True`，则字段在反序列化时不会被使用，默认为 `False`。
    :param write_only: 如果为 `True`，则字段在序列化时不会被使用，默认为 `False`。
    """

    def __init__(
        self,
        *,
        attr: t.Optional[str] = None,
        alias: t.Optional[str] = None,
        read_only: bool = False,
        write_only: bool = False,
        **kwargs,
    ):
        self._model: t.Optional[Model] = None
        self.__name = None
        self.__attr = attr
        self.__alias = alias
        self.read_only = read_only
        self.write_only = write_only

    @property
    def _name(self):
        assert self.__name is not None, f"{self!r} is not a field."
        return self.__name

    @_name.setter
    def _name(self, value):
        assert self.__name is None, self.__name
        self.__name = value

    @property
    def _alias(self) -> str:
        return self.__alias or self._name

    @property
    def _attr(self) -> str:
        return self.__attr or self._name

    def _serialization_fget(self, data):
        """获取待序列化的值。"""

        hook = get_hook(self._model, ("serialization_fget", self._name))
        if hook:
            return hook(data)

        if isinstance(data, Mapping):
            return data[self._attr]
        return getattr(data, self._attr)


class Schema(Field, metaclass=SchemaMeta):
    """
    :param required: |AsField| 在反序列化时，判断字段是否必需提供。默认必需，可设为 `False` 或设置 ``default`` 参数使其变为非必需。

        .. code-block::

            >>> class User(Model):
            ...     username = String()
            ...     address = String(required=False)

            >>> User().deserialize({})
            Traceback (most recent call last):
                ...
            django_openapi_schema.exceptions.ValidationError: [{'msgs': ['This field is required.'], 'loc': ['username']}]

    :param default: |AsField| 如果字段非必需，且设置了默认值，那么反序列化时如未提供该字段数据，则使用该默认值填充。该参数可设为一个无参函数，默认值将使用该函数的结果。

        .. code-block::

            >>> from datetime import date

            >>> class User(Model):
            ...     username = String(default='未命名用户')
            ...     address = String(default=lambda: '未提供')  # 使用函数设置默认值

            >>> User().deserialize({})
            {'username': '未命名用户', 'address': '未提供'}

    :param choices: 如果提供，则反序列时的值必须是选择中的一个。

        .. code-block::

            >>> fruit = String(choices=['apple', 'watermelon', 'grape'])

            >>> fruit.deserialize('apple')
            'apple'

            >>> fruit.deserialize('banana')
            Traceback (most recent call last):
                ...
            django_openapi_schema.exceptions.ValidationError: [{'msgs': ["The value must be one of 'apple', 'watermelon', 'grape'."]}]

    :param nullable: 设置为 `True`，序列化和反序列化将允许输出 `None`，默认 `False`。

        .. code-block::

            >>> String(nullable=True).serialize(None) is None
            True

            >>> String(nullable=True).deserialize(None) is None
            True

        .. code-block::

            >>> String().serialize(None)
            Traceback (most recent call last):
                ...
            ValueError: The value cannot be None.

            >>> String().deserialize(None)
            Traceback (most recent call last):
                ...
            django_openapi_schema.exceptions.ValidationError: [{'msgs': ['The value cannot be null.']}]

    :param description: 在 |OAS| 中提供描述内容。
    :param validators: 用于设置反序列化校验函数。

        .. code-block::

            >>> def validate(value):
            ...     if value <= 0:
            ...         raise ValidationError('不是一个正整数')

            >>> Integer(validators=[validate]).deserialize(-1)
            Traceback (most recent call last):
                ...
            django_openapi_schema.exceptions.ValidationError: [{'msgs': ['不是一个正整数']}]
    """

    meta: MetaOptions

    class Meta:
        """Schema 配置选项。"""

        #: 声明 `OAS Data Type <https://spec.openapis.org/oas/v3.0.3#dataTypes>`_，自动被子类延用。
        data_type: str

        #: 声明 `OAS Data Type Format <https://spec.openapis.org/oas/v3.0.3#dataTypeFormat>`_，自动被子类延用。
        data_format: t.Optional[str]

    def __init__(
        self,
        *,
        required: t.Optional[bool] = None,
        default: t.Union[t.Any, t.Callable[[], t.Any]] = EMPTY,
        nullable: bool = False,
        validators: t.Optional[t.List[t.Callable[[t.Any], t.Any]]] = None,
        choices: t.Optional[t.Iterable] = None,
        description: str = "",
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.options = dict(
            required=required,
            default=default,
            description=description,
            nullable=nullable,
            validators=validators,
            choices=choices,
            **kwargs,
        )

        self._validators = validators or []
        if choices is not None:
            self._validators.append(_validators.OneOf((choices)))

    @property
    def _required(self) -> bool:
        assert self._model is not None
        if self._model._required_fields == "__all__":
            return True

        if self._model._required_fields is None:
            required = self.options["required"]
            if isinstance(required, bool):
                return required
            return self.options["default"] is EMPTY

        return self._name in self._model._required_fields  # type: ignore

    def deserialize(self, value):
        """对数据进行反序列化操作。"""
        if value is None:
            if self.options["nullable"]:
                return value
            else:
                raise ValidationError("The value cannot be null.")

        value = self._deserialize(value)

        def get_validators():
            # field hook
            if self._model is not None:
                for hook in iter_hooks(self._model, ("validator", self._name)):
                    yield hook

            # schema hook
            for hook in iter_hooks(self, ("validator", None)):
                yield hook

            # self
            yield from self._validators

        error = ValidationError()
        for validator in get_validators():
            try:
                validator(value)
            except ValidationError as exc:
                error._concat_error(exc)
        if error._nonempty:
            raise error

        return value

    @property
    def __is_field(self):
        return self._model is not None

    def _deserialize(self, value):
        return value

    def serialize(self, value):
        """对数据进行序列化操作。"""
        try:
            if value is None:
                if self.options["nullable"]:
                    return value
                else:
                    if self.__is_field:
                        raise ValueError(f"The field {self._name!r} cannot be {value}.")
                    raise ValueError(f"The value cannot be {value}.")
            return self._serialize(value)
        except Exception as exc:
            raise exc

    def _serialize(self, value):
        return value

    def __openapispec__(self, spec):
        return dict(
            type=self.meta["data_type"],
            default=None
            if (self.options["default"] is EMPTY or callable(self.options["default"]))
            else self.options["default"],
            # # # example=None if self.example is EMPTY else _spec.Skip(
            # # #     self.example() if callable(self.example) else self.example),
            description=self.options["description"] or None,
            readOnly=default_as_none(self.read_only, False),
            writeOnly=default_as_none(self.write_only, False),
            enum=self.options["choices"],
            nullable=default_as_none(self.options["nullable"], False),
            format=self.meta["data_format"],
            # deprecated=_spec.default_as_none(self.deprecated, False),
        )


class FieldMapping(t.Mapping[str, Schema]):
    def __init__(self, **kwargs):
        self.__field_dict = kwargs

    def __getitem__(self, item) -> Schema:
        return self.__field_dict[item]

    def __len__(self):
        return len(self.__field_dict)

    def __iter__(self):
        return iter(self.__field_dict)


class ModelMeta(SchemaMeta):
    _fields: FieldMapping

    def __new__(mcs, classname, bases, attrs: dict):
        fields: t.Dict[str, Field] = {}

        # inherit fields
        for base in bases:
            if isinstance(base, ModelMeta):
                for field in base._fields.values():
                    fields.setdefault(field._name, field)  # type: ignore

        for name, value in attrs.copy().items():
            if isinstance(value, Field):
                value._name = name
                fields[name] = value
                del attrs[name]
        attrs["_fields"] = FieldMapping(**fields)
        return super().__new__(mcs, classname, bases, attrs)


INCLUDE = "include"
EXCLUDE = "exclude"
ERROR = "error"


class Model(Schema, metaclass=ModelMeta):
    """
    :param required_fields: 覆盖原有的必需字段的配置。设为空列表则所有字段为非必需，也可设为 ``"__all__"`` 指定所有字段为必需。

        .. code-block::

            >>> class User(Model):
            ...     username = String()
            ...     address = String(required=False)

        .. code-block::
            :caption: 设为 [] 指定所有字段为非必需

            >>> User(required_fields=[]).deserialize({})
            {}

        .. code-block::
            :caption: 设为 "__all__" 指定所有字段为必需

            >>> import pprint

            >>> try:
            ...     User(required_fields='__all__').deserialize({})
            ... except ValidationError as exc:
            ...     pprint.pprint(exc.format_errors())
            [{'loc': ['username'], 'msgs': ['This field is required.']},
             {'loc': ['address'], 'msgs': ['This field is required.']}]

        .. code-block::
            :caption: 指定部分字段为必需

            >>> try:
            ...     User(required_fields=['address']).deserialize({})
            ... except ValidationError as exc:
            ...     pprint.pprint(exc.format_errors())
            [{'loc': ['address'], 'msgs': ['This field is required.']}]

    :param unknown_fields: 该参数决定了在反序列化时如何处理未知字段。

        .. code-block::

            >>> class User(Model):
            ...     name = String()
            ...     age = Integer()

            >>> data = {'name': '张三', 'age': 24, 'address': '北京'}

        .. code-block::
            :caption: exclude (默认)

            >>> User().deserialize(data)
            {'name': '张三', 'age': 24}

        .. code-block::
            :caption: include

            >>> User(unknown_fields='include').deserialize(data)
            {'name': '张三', 'age': 24, 'address': '北京'}

        .. code-block::
            :caption: error

            >>> User(unknown_fields='error').deserialize(data)
            Traceback (most recent call last):
                ...
            django_openapi_schema.exceptions.ValidationError: [{'msgs': ['Unknown field.'], 'loc': ['address']}]
    """

    class Meta:
        data_type = "object"

    _fields: FieldMapping

    def __init__(
        self,
        required_fields: t.Union[t.Iterable[str], str, None] = None,
        unknown_fields: str = EXCLUDE,
        **kwargs,
    ):
        super().__init__(**kwargs)

        # unknown fields
        unknown_fields_choices = [INCLUDE, EXCLUDE, ERROR]
        if unknown_fields not in unknown_fields_choices:
            raise ValueError(
                "unknown_fields must be one of "
                f'{", ".join([repr(i) for i in unknown_fields_choices])}.'
            )
        self._unknown_fields = unknown_fields

        # required fields
        if isinstance(required_fields, Iterable) and not isinstance(
            required_fields, str
        ):
            required_fields = set(required_fields)
            unknown_field_names = required_fields - self._fields.keys()
            assert (
                not unknown_field_names
            ), f"Unknown field names: {unknown_field_names}."
        else:
            assert (
                required_fields == "__all__" or required_fields is None
            ), f"Invalid required_fields: {required_fields}."
        self._required_fields = required_fields

        # fields
        fields = {}
        for name, field in self.__class__._fields.items():
            field_copy = copy.copy(field)

            assert field_copy._model is None
            field_copy._model = self

            fields[name] = field_copy
        self._fields = FieldMapping(**fields)

    @staticmethod
    def from_dict(fields: t.Dict[str, Field]) -> t.Type["Model"]:
        # 过滤掉非 Schema 字段
        attrs: dict = {k: v for k, v in fields.items() if isinstance(v, Field)}
        klass = type("GeneratedSchema", (Model,), attrs)
        return t.cast(t.Type[Model], klass)

    def _deserialize(self, value: dict):
        data = copy.copy(value)
        del value

        rv = {}
        error = ValidationError()

        for field in self._fields.values():
            if field.read_only:
                continue

            try:
                val = data.pop(field._alias)
            except KeyError:
                val = EMPTY

            if val is EMPTY:
                if field._required:
                    error._set_index_error(
                        field._alias,  # type: ignore
                        ValidationError("This field is required."),
                    )

                default = field.options["default"]
                if default is not EMPTY:
                    rv[field._attr] = default() if callable(default) else default

                continue

            try:
                rv[field._attr] = field.deserialize(val)
            except ValidationError as exc:
                error._set_index_error(field._alias, exc)  # type: ignore

        if self._unknown_fields == EXCLUDE:
            pass
        elif self._unknown_fields == INCLUDE:
            rv.update(data)
        elif self._unknown_fields == ERROR and data:
            for key in data:
                error._set_index_error(key, ValidationError("Unknown field."))

        if error._nonempty:
            raise error

        return rv

    def _serialize(self, value):
        rv = {}
        for field in self._fields.values():
            if field.write_only:
                continue
            field_value = field._serialization_fget(value)
            try:
                rv[field._alias] = field.serialize(field_value)
            except Exception as exc:
                raise exc

        return rv

    def __openapispec__(self, spec):
        def get_required_list():
            required = []
            for field in self._fields.values():
                if field._required:
                    required.append(field._alias)
            return required

        result = super().__openapispec__(spec)
        properties = {}
        for field in self._fields.values():
            properties[field._alias] = spec.parse(field)
        result.update(
            {
                "properties": properties,
                "required": get_required_list(),
            }
        )
        return result


class String(Schema):
    """
    :param pattern: 如果设置，则反序列化字符串必需匹配正则表达式。
    :param min_length: 如果设置，则反序列化字符串必须大于等于最小长度。
    :param max_length: 设置设置，则反序列化字符串必须小于等于最大长度。
    """

    class Meta:
        data_type = "string"

    def __init__(
        self,
        *,
        pattern: t.Union[str, re.Pattern, None] = None,
        min_length: t.Optional[int] = None,
        max_length: t.Optional[int] = None,
        **kwargs,
    ):
        super().__init__(
            **kwargs,
            min_length=min_length,
            max_length=max_length,
        )

        # pattern
        self.__pattern = None
        if pattern:
            regexp = _validators.RegExpValidator(pattern)
            self.__pattern = regexp.pattern.pattern
            self._validators.append(regexp)

        # length
        if min_length is not None or max_length is not None:
            self._validators.append(_validators.LengthValidator(min_length, max_length))

    def _deserialize(self, value) -> str:
        return str(value)

    def _serialize(self, value) -> str:
        return str(value)

    def __openapispec__(self, spec):
        result = super().__openapispec__(spec)
        result.update(
            pattern=self.__pattern,
            minLength=self.options["min_length"],
            maxLength=self.options["max_length"],
        )
        return result


class Number(Schema):
    def __init__(
        self,
        gt=None,
        gte=None,
        lt=None,
        lte=None,
        multiple_of=None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._gt = gt
        self._gte = gte
        self._lt = lt
        self._lte = lte
        if any(i is not None for i in (gt, gte, lt, lte)):
            self._validators.append(
                _validators.RangeValidator(gt=gt, gte=gte, lt=lt, lte=lte)
            )

        self._multiple_of = multiple_of
        if multiple_of is not None:
            self._validators.append(_validators.MultipleOfValidator(self._multiple_of))

    def __openapispec__(self, spec, **kwargs):
        result = super().__openapispec__(spec, **kwargs)
        result.update(
            maximum=self._lte if self._lt is None else self._lt,
            exclusiveMaximum=self._lt is not None or None,
            minimum=self._gte if self._gt is None else self._gt,
            exclusiveMinimum=self._gt is not None or None,
            multipleOf=self._multiple_of,
        )
        return result


class Integer(Number):
    class Meta:
        data_type = "integer"

    def _deserialize(self, value) -> int:
        return int(value)

    def _serialize(self, value) -> int:
        return int(value)


class Float(Number):
    class Meta:
        data_type = "number"
        data_format = "float"

    def _deserialize(self, value) -> float:
        return float(value)

    def _serialize(self, value):
        return float(value)


class Boolean(Schema):
    class Meta:
        data_type = "boolean"


class Datetime(Schema):
    class Meta:
        data_type = "string"
        data_format = "date-time"

    def _deserialize(self, value: str) -> datetime.datetime:
        return isoparse(value)

    def _serialize(self, value: datetime.datetime) -> str:
        return value.isoformat()


class Date(Schema):
    class Meta:
        data_type = "string"
        data_format = "date"

    def _deserialize(self, value) -> datetime.date:
        return isoparse(value).date()


class Any(Schema):
    class Meta:
        data_type = None

    def _deserialize(self, value):
        return value

    def _serialize(self, value):
        return value

    def __openapispec__(self, spec):
        return spec.Protect(super().__openapispec__(spec))


class List(Schema):
    """
    :param item: 定义元素类型，默认为 `Any`。
    :param min_items: 如果设置，则反序列化列表长度必须大于等于最小长度。
    :param max_items: 如果设置，则反序列化列表长度必须小于等于最大长度。
    :param unique_items: 如果为 `True`，则反序列化的所有元素必须唯一，默认 `False`。

    .. code-block::

        >>> from collections import namedtuple

        >>> Book = namedtuple('Book', ['title', 'author'])
        >>> books = [
        ...     Book(title='三体', author='刘慈欣'),
        ...     Book(title='活着', author='余华'),
        ... ]

        >>> class BookSchema(Model):
        ...     title = String()
        ...     author = String()

        >>> List(BookSchema).serialize(books)
        [{'title': '三体', 'author': '刘慈欣'}, {'title': '活着', 'author': '余华'}]
    """

    class Meta:
        data_type = "array"

    def __init__(
        self,
        item: t.Union[Schema, t.Type[Schema], None] = None,
        *,
        min_items: t.Optional[int] = None,
        max_items: t.Optional[int] = None,
        unique_items: bool = False,
        **kwargs,
    ):
        super().__init__(
            **kwargs,
            min_items=min_items,
            max_items=max_items,
            unique_items=unique_items,
        )
        self.__item: Schema = make_instance(item or Any)
        if max_items is not None or min_items is not None:
            self._validators.append(_validators.LengthValidator(min_items, max_items))
        if unique_items:
            self._validators.append(_validators.unique_validate)

    def _deserialize(self, value):
        rv = []
        error = ValidationError()

        for index, item in enumerate(value):
            try:
                rv.append(self.__item.deserialize(item))
            except ValidationError as exc:
                error._set_index_error(index, exc)

        if error._nonempty:
            raise error
        return rv

    def _serialize(self, value):
        rv = []
        for item in value:
            rv.append(self.__item.serialize(item))
        return rv

    def __openapispec__(self, spec):
        result = super().__openapispec__(spec)
        result.update(
            items=spec.parse(self.__item),
            maxItems=self.options["max_items"],
            minItems=self.options["min_items"],
            uniqueItems=default_as_none(self.options["unique_items"], False),
        )
        return result


class Dict(Schema):
    """
    :param value: 定义值类型，默认为 `Any`。
    :param min_properties: 如果设置，则反序列化字典长度必须大于等于最小长度。
    :param max_properties: 如果设置，则反序列化字典长度必须小于等于最大长度。
    """

    class Meta:
        data_type = "object"

    def __init__(
        self,
        value: t.Union[Schema, t.Type[Schema], None] = None,
        *,
        max_properties: t.Optional[int] = None,
        min_properties: t.Optional[int] = None,
        **kwargs,
    ):
        super().__init__(
            **kwargs,
            max_properties=max_properties,
            min_properties=min_properties,
        )
        self.__value: Schema = make_instance(value or Any)

        if min_properties is not None or max_properties is not None:
            self._validators.append(
                _validators.LengthValidator(min_properties, max_properties)
            )

    def _deserialize(self, obj):
        if not isinstance(obj, dict):
            raise ValidationError("Not a valid dict object.")
        rv = {}
        for key, val in obj.items():
            try:
                val = self.__value.deserialize(val)
            except ValidationError as e:
                raise ValidationError("The value %s" % e)
            rv[key] = val
        return rv

    def _serialize(self, obj):
        return {key: self.__value.serialize(val) for key, val in obj.items()}

    def __openapispec__(self, spec) -> dict:
        result = super().__openapispec__(spec)
        result.update(
            additionalProperties=spec.parse(self.__value),
            maxProperties=self.options["max_properties"],
            minProperties=self.options["min_properties"],
        )
        return result


class AnyOf(Schema):
    def __init__(self, schemas: t.List[Schema], **kwargs) -> None:
        super().__init__(**kwargs)
        self.__schemas = schemas


class Password(String):
    class Meta:
        data_format = "password"
