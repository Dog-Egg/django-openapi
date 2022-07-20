import functools
import typing
from decimal import Decimal
from collections import ChainMap

from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError

from openapi.schema import schemas
from openapi.schema.exceptions import ValidationError

__all__ = ['model2schema']


class GeneralConvertor:
    schema_cls = None

    def __init__(self, schema_cls=None):
        if schema_cls is not None:
            self.schema_cls = schema_cls

    def convert(self, field):
        kwargs = ChainMap(self._get_common_kwargs(field), self._get_extra_kwargs(field))
        return self.schema_cls(**kwargs)

    def _get_extra_kwargs(self, field) -> dict:
        return {}

    def _get_common_kwargs(self, field: models.Field):
        default = schemas.undefined
        if field.default is models.NOT_PROVIDED:
            required = True
        else:
            required = False
            if not callable(field.default):
                default = field.default

        kwargs = dict(
            serialize_only=(not field.editable or field.primary_key),
            required=required,
            default=default,
            nullable=field.null,
            enum=field.choices and [x[0] for x in field.choices],
            validators=self._get_validators(field.validators.copy()),
            description=self._get_description(field),
            # allow_blank != field.blank # blank 是 django form 验证使用，和 allow_blank 不一样
        )
        if isinstance(field.max_length, int):
            kwargs.update(max_length=field.max_length)
        return kwargs

    @staticmethod
    def _get_description(field):
        verbose_name, help_text = (str(s) for s in [
            getattr(field, '_verbose_name', field.verbose_name),
            field.help_text
        ])
        if verbose_name:
            verbose_name = '### %s' % verbose_name
        return '\n\n'.join(x for x in (verbose_name, help_text) if x)

    def _get_validators(self, validators):
        return [self._django_validator_wrap(v) for v in validators]

    @staticmethod
    def _django_validator_wrap(validator):
        @functools.wraps(validator)
        def wrapper(*args, **kwargs):
            try:
                return validator(*args, **kwargs)
            except DjangoValidationError as exc:
                raise ValidationError(list(exc)[0]) from exc

        return wrapper


class CharConvertor(GeneralConvertor):
    schema_cls = schemas.String

    def _get_validators(self, validators):
        validators.pop()  # 和 char 验证器重复
        return super()._get_validators(validators)


class DecimalConvertor(GeneralConvertor):
    schema_cls = schemas.Float

    def _get_extra_kwargs(self, field: models.DecimalField) -> dict:
        lt = 10 ** (field.max_digits - field.decimal_places)
        multiple_of = Decimal('0.1') ** field.decimal_places
        return dict(lt=lt, multiple_of=float(multiple_of))


MODEL_FIELD_CONVERTORS = {
    models.AutoField: GeneralConvertor(schemas.Integer),
    models.BigAutoField: GeneralConvertor(schemas.Integer),
    models.BigIntegerField: GeneralConvertor(schemas.Integer),
    models.BooleanField: GeneralConvertor(schemas.Boolean),
    models.NullBooleanField: GeneralConvertor(schemas.Boolean),
    models.CharField: CharConvertor(),
    models.DateField: GeneralConvertor(schemas.Date),
    models.DateTimeField: GeneralConvertor(schemas.Datetime),
    models.EmailField: GeneralConvertor(schemas.String),
    models.FileField: GeneralConvertor(schemas.File),
    models.FloatField: GeneralConvertor(schemas.Float),
    models.IntegerField: GeneralConvertor(schemas.Integer),
    models.PositiveBigIntegerField: GeneralConvertor(schemas.Integer),
    models.PositiveIntegerField: GeneralConvertor(schemas.Integer),
    models.PositiveSmallIntegerField: GeneralConvertor(schemas.Integer),
    models.DecimalField: DecimalConvertor(),
}


def model2schema(model_class: typing.Type[models.Model]):
    fields = {}
    for field in model_class._meta.fields:
        convertor = MODEL_FIELD_CONVERTORS.get(type(field))
        if not convertor:
            continue
        fields[field.name] = convertor.convert(field)
    return schemas.Model.from_dict(fields, name=model_class.__name__)
