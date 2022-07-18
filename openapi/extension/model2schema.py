import functools
import typing

from django.db import models
from django.core.exceptions import ValidationError as DjangoValidationError

from openapi.schema import schemas
from openapi.schema.exceptions import ValidationError

__all__ = ['model2schema']

MODEL_FIELD_2_SCHEMA_FIELD = {
    models.AutoField: schemas.Integer,
    models.BigAutoField: schemas.Integer,
    models.BigIntegerField: schemas.Integer,
    models.BooleanField: schemas.Boolean,
    models.NullBooleanField: schemas.Boolean,
    models.CharField: schemas.String,
    models.DateField: schemas.Date,
    models.DateTimeField: schemas.Datetime,
    models.EmailField: schemas.String,
    models.FileField: schemas.File,
    models.FloatField: schemas.Float,
    models.IntegerField: schemas.Integer,
    models.PositiveBigIntegerField: schemas.Integer,
    models.PositiveIntegerField: schemas.Integer,
    models.PositiveSmallIntegerField: schemas.Integer,
}


def _get_description(model_field):
    verbose_name, help_text = (str(s) for s in [
        getattr(model_field, '_verbose_name', model_field.verbose_name),
        model_field.help_text
    ])
    if verbose_name:
        verbose_name = '### %s' % verbose_name
    return '\n\n'.join(x for x in (verbose_name, help_text) if x)


def _django_validator_wrap(validator):
    @functools.wraps(validator)
    def wrapper(*args, **kwargs):
        try:
            return validator(*args, **kwargs)
        except DjangoValidationError as exc:
            raise ValidationError(list(exc)[0]) from exc

    return wrapper


def model_field_to_schema_field(model_field: models.Field):
    schema_class: typing.Type[schemas.Schema] = MODEL_FIELD_2_SCHEMA_FIELD.get(type(model_field))
    if schema_class is None:
        return

    default = schemas.undefined
    if model_field.default is models.NOT_PROVIDED:
        required = True
    else:
        required = False
        if not callable(model_field.default):
            default = model_field.default

    kwargs = {}
    if isinstance(model_field.max_length, int):
        kwargs.update(max_length=model_field.max_length)

    return schema_class(
        serialize_only=(not model_field.editable or model_field.primary_key),  # FIXME
        required=required,
        default=default,
        nullable=model_field.null,
        enum=model_field.choices and [x[0] for x in model_field.choices],
        validators=[_django_validator_wrap(v) for v in model_field.validators],
        description=_get_description(model_field),
        **kwargs,
    )


def model2schema(model_class: typing.Type[models.Model]):
    fields = {}
    for model_field in model_class._meta.fields:
        model_field: models.Field
        schema_field = model_field_to_schema_field(model_field)
        if schema_field:
            fields[model_field.name] = schema_field
    return schemas.Model.from_dict(fields, name=model_class.__name__)
