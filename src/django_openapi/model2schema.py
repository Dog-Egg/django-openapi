import inspect
import typing as t
from decimal import Decimal

import django
from django.core.validators import DecimalValidator, MaxLengthValidator
from django.db import models

from django_openapi.utils.django import django_validator_wraps

from . import schema


def filter_defaults(kwargs: dict):
    _kwargs = kwargs.copy()
    defaults = {
        "required": None,
        "read_only": False,
        "default": schema.EMPTY,
        "choices": None,
        "validators": [],
        "description": "",
        "nullable": False,
    }
    for k in kwargs.keys():
        if k in defaults and defaults[k] == kwargs[k]:
            del _kwargs[k]
    return _kwargs


class Parser:
    schemaclass: t.Type[schema.Schema]

    def __init__(self, schemaclass=None):
        if schemaclass is not None:
            self.schemaclass = schemaclass

    def parse(self, field):
        kwargs = {
            **self.get_common_kwargs(field),
            **self.get_own_kwargs(field),
        }

        # 删除有默认值的参数，方便测试
        return self.schemaclass, filter_defaults(kwargs)

    def get_own_kwargs(self, field) -> dict:
        return {}

    def get_common_kwargs(self, field: models.Field):
        required = None

        # default
        default = schema.EMPTY
        if field.default is not models.NOT_PROVIDED:
            if not callable(field.default):
                default = field.default
            else:
                required = False

        # required
        if field.blank:
            required = False

        kwargs = dict(
            read_only=(not field.editable or field.primary_key),
            required=required,
            default=default,
            nullable=field.null,
            choices=field.choices and [x[0] for x in field.choices],
            validators=[
                django_validator_wraps(v)
                for v in self.get_validators(field.validators.copy())
            ],
            description=self.get_description(field),
        )
        if isinstance(field.max_length, int):
            kwargs.update(max_length=field.max_length)

        return kwargs

    @staticmethod
    def get_description(field):
        contents = tuple(
            str(item)
            for item in (
                getattr(field, "_verbose_name", field.verbose_name),
                field.help_text,
                "\n".join(
                    [
                        f"- %s: %s" % (choice[0], choice[1])
                        for choice in field.choices or []
                    ]
                ),
            )
            if item
        )
        return "\n\n".join(contents)

    def get_validators(self, validators):
        return validators


class CharParser(Parser):
    schemaclass = schema.String

    def get_validators(self, validators):
        # 验证器重复
        return [v for v in validators if not isinstance(v, MaxLengthValidator)]


class ForeignKeyParser(Parser):
    def parse(self, field):
        target_field = field.target_field
        parser = match_parser(type(target_field))
        schemaclass, kwargs = parser.parse(target_field)
        self_kwargs = self.get_common_kwargs(field)
        kwargs.update(self_kwargs)
        return schemaclass, filter_defaults(kwargs)


class FileParser(Parser):
    schemaclass = schema.File

    def get_common_kwargs(self, field):
        kwargs = super().get_common_kwargs(field)
        kwargs.pop("max_length")
        return kwargs


class DecimalParser(Parser):
    schemaclass = schema.Float

    def get_validators(self, validators):
        for validator in validators:
            if isinstance(validator, DecimalValidator):

                def wrapper(value):
                    if isinstance(value, float):
                        value = Decimal(str(value))
                    return validator(value)

                yield wrapper
            else:
                yield validator


MODEL_FIELD_PARSERS = {
    models.BooleanField: Parser(schema.Boolean),
    models.CharField: CharParser(),
    models.IntegerField: Parser(schema.Integer),
    models.DateField: Parser(schema.Date),
    models.DateTimeField: Parser(schema.Datetime),
    models.FileField: FileParser(),
    models.DecimalField: DecimalParser(),
    models.ForeignKey: ForeignKeyParser(),
    models.JSONField: Parser(schema.Any),
}
if django.VERSION >= (3, 1):
    MODEL_FIELD_PARSERS.update({})


def match_parser(
    fieldclass: t.Type[models.Field],
) -> Parser:
    """
    从 MODEL_FIELD_PARSERS 查找可以直接使用的解析器，
    或使用 field class 父类查找是否有匹配的解析器。
    """
    for cls in inspect.getmro(fieldclass):
        if cls in MODEL_FIELD_PARSERS:
            return MODEL_FIELD_PARSERS[cls]
    raise NotImplementedError(fieldclass)


def model2schema(
    modelcls: t.Type[models.Model],
    *,
    include_fields: t.Optional[t.List[str]] = None,
    exclude_fields: t.Optional[t.List[str]] = None,
    extra_kwargs: t.Optional[t.Dict[str, dict]] = None,
) -> t.Type[schema.Model]:
    if include_fields is not None and exclude_fields is not None:
        raise ValueError("Cannot set both 'include_fields' and 'exclude_fields'.")
    _include_fields = None if include_fields is None else set(include_fields)
    _exclude_fields = None if exclude_fields is None else set(exclude_fields)

    fields = {}
    for fieldname, (schemaclass, kwargs) in parse(modelcls).items():
        if _include_fields is not None:
            if fieldname in _include_fields:
                _include_fields.remove(fieldname)
            else:
                continue

        if _exclude_fields is not None:
            if fieldname in _exclude_fields:
                _exclude_fields.remove(fieldname)
                continue

        if extra_kwargs and fieldname in extra_kwargs:
            kwargs.update(extra_kwargs.pop(fieldname))

        fields[fieldname] = schemaclass(**kwargs)

    if _include_fields:
        raise ValueError(f"Unknown include_fields: {_include_fields}.")
    if _exclude_fields:
        raise ValueError(f"Unknown exclude_fields: {_exclude_fields}.")

    if extra_kwargs:
        raise ValueError(
            f"Unknown extra_kwargs keys: {', '.join(extra_kwargs.keys())}."
        )

    return schema.Model.from_dict(fields)


def parse(
    modelclass: t.Type[models.Model],
) -> t.Dict[str, t.Tuple[t.Type[schema.Schema], dict]]:
    result = {}
    for field in modelclass._meta.fields:
        fieldname = field.attname
        parser = match_parser(type(field))
        result[fieldname] = parser.parse(field)
    return result
