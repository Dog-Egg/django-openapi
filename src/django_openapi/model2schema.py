import inspect
import typing
from decimal import Decimal

import django
from django.core.validators import DecimalValidator, MaxLengthValidator
from django.db import models
from django.db.models.fields.files import FieldFile

from django_openapi.utils.django import django_validator_wraps

try:
    from django.db.models import JSONField
except ImportError:
    JSONField = None

from . import schema
from .utils.functional import Filter


class Convertor:
    schema_cls: typing.Type[schema.Schema]

    def __init__(self, schema_cls=None):
        if schema_cls is not None:
            self.schema_cls = schema_cls

    def convert(self, field, extra_kwargs=None):
        kwargs = {
            **self.get_common_kwargs(field),
            **self.get_own_kwargs(field),
        }
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        return self.schema_cls(**kwargs)

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


class CharConvertor(Convertor):
    schema_cls = schema.String

    def get_validators(self, validators):
        # 验证器重复
        return [v for v in validators if not isinstance(v, MaxLengthValidator)]


class DecimalConvertor(Convertor):
    schema_cls = schema.Float

    def get_validators(self, validators):
        # 验证器冲突
        return [v for v in validators if not isinstance(v, DecimalValidator)]

    def get_own_kwargs(self, field: models.DecimalField) -> dict:
        maximum = 10 ** (field.max_digits - field.decimal_places)
        multiple_of = Decimal("0.1") ** field.decimal_places
        return dict(
            maximum=maximum, exclusive_minimum=True, multiple_of=float(multiple_of)
        )


class ForeignKeyConvertor(Convertor):
    def convert(self, field, extra_kwargs=None):
        target_field = field.target_field
        convertor = match_convertor(type(target_field))
        if not convertor:
            return

        kwargs = self.get_common_kwargs(field)
        if extra_kwargs:
            kwargs.update(extra_kwargs)
        return convertor.convert(target_field, extra_kwargs=kwargs)


MODEL_FIELD_CONVERTORS = {
    # models.AutoField: Convertor(schema.Integer),
    # models.BigAutoField: Convertor(schema.Integer),
    # models.BigIntegerField: Convertor(schema.Integer),
    models.BooleanField: Convertor(schema.Boolean),
    # models.NullBooleanField: Convertor(schema.Boolean),
    models.CharField: CharConvertor(),
    models.IntegerField: Convertor(schema.Integer),
    # models.TextField: Convertor(schemas.String),
    models.DateField: Convertor(schema.Date),
    models.DateTimeField: Convertor(schema.Datetime),
    # models.EmailField: Convertor(schemas.String),
    # models.URLField: Convertor(schemas.String),
    models.FileField: Convertor(schema.File),
    # models.FloatField: Convertor(schemas.Float),
    # models.IntegerField: Convertor(schemas.Integer),
    # models.PositiveIntegerField: Convertor(schemas.Integer),
    # models.PositiveSmallIntegerField: Convertor(schemas.Integer),
    models.DecimalField: DecimalConvertor(),
    models.ForeignKey: ForeignKeyConvertor(),
    # JSONField: Convertor(schema.Any),
}
if django.VERSION >= (3, 1):
    MODEL_FIELD_CONVERTORS.update(
        {
            # models.PositiveBigIntegerField: Convertor(schemas.Integer),
        }
    )


def match_convertor(
    fieldclass: typing.Type[models.Field],
) -> typing.Optional[Convertor]:
    """
    从 MODEL_FIELD_CONVERTORS 查找可以直接使用的转换器，
    或使用 field class 父类查找是否有匹配的转换器。
    """
    for cls in inspect.getmro(fieldclass):
        if cls in MODEL_FIELD_CONVERTORS:
            return MODEL_FIELD_CONVERTORS[cls]
    raise NotImplementedError(fieldclass)


def model2schema(
    model: typing.Type[models.Model],
    *,
    include_fields=None,
    extra_kwargs=None,
) -> typing.Type[schema.Model]:
    extra_kwargs = extra_kwargs or {}

    fields = {}
    # noinspection PyUnresolvedReferences,PyProtectedMember
    for field in model._meta.fields:
        field: models.Field  # type: ignore
        model_field_name = field.attname
        if include_fields is not None and model_field_name not in include_fields:
            continue
        convertor = match_convertor(type(field))
        if not convertor:
            continue
        fields[model_field_name] = convertor.convert(
            field,
            extra_kwargs=extra_kwargs.pop(model_field_name, None),
        )

    # 避免修改 model 字段名后忘记修改此处，所以对没用的 extra_kwargs 报错
    if extra_kwargs:
        raise ValueError(
            "Redundant extra_kwargs keys: %s." % ", ".join(extra_kwargs.keys())
        )

    return schema.Model.from_dict(fields)
