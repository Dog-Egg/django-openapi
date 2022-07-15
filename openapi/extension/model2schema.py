import typing

from django.db import models

from openapi.schema import schemas

DJANGO_MODEL_FIELD_2_SCHEMA_FIELD = {
    models.AutoField: schemas.Integer,
    models.BigAutoField: schemas.Integer,
    models.BigIntegerField: schemas.Integer,
    # models.BinaryField: TODO
    models.BooleanField: schemas.Boolean,
    models.NullBooleanField: schemas.Boolean,
    models.CharField: schemas.String,
    models.DateField: schemas.Date,
    models.DateTimeField: schemas.Datetime,
    # models.DecimalField: TODO
    # models.DurationField: TODO
    models.EmailField: schemas.String,  # TODO
    models.FileField: schemas.File,  # TODO
    # models.FilePathField: TODO
    models.FloatField: schemas.Float,
    # models.GenericIPAddressField TODO
    # models.ImageField:  TODO
    models.IntegerField: schemas.Integer,
    # models.JSONField: TODO
    models.PositiveBigIntegerField: schemas.Integer,  # TODO
    models.PositiveIntegerField: schemas.Integer,  # TODO
    models.PositiveSmallIntegerField: schemas.Integer,  # TODO
    # ... 没写完
}


def model2schema(model_class: typing.Type[models.Model]):
    fields = {}
    for model_field in model_class._meta.fields:
        model_field: models.Field
        schema_class = DJANGO_MODEL_FIELD_2_SCHEMA_FIELD[type(model_field)]

        kwargs = {}
        if schema_class is schemas.String:
            kwargs['max_length'] = model_field.max_length

        required = True
        default = schemas.undefined
        if callable(model_field.default):
            required = False
        else:
            if model_field.default is not models.NOT_PROVIDED:
                default = model_field.default

        fields[model_field.name] = schema_class(
            required=required,
            default=default,
            nullable=model_field.null,
            # model_field.blank # TODO
            enum=model_field.choices and [x[0] for x in model_field.choices],
            deserialize_only=not model_field.editable,
            description=' | '.join(x for x in (model_field.verbose_name, model_field.help_text) if x),
            **kwargs,
        )
    return schemas.Model.from_dict(fields)
