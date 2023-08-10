from django.conf import settings

import django_openapi_schema as schema

__all__ = (
    "Path",
    "File",
    "Datetime",
)


class Path(schema.String):
    pass


class File(schema.Schema):
    class Meta:
        data_type = "string"
        data_format = "binary"

    def _serialize(self, obj):
        return obj.url


class Datetime(schema.Datetime):
    def __init__(self, **kwargs):
        kwargs.setdefault("with_tz", settings.USE_TZ)
        super().__init__(**kwargs)
