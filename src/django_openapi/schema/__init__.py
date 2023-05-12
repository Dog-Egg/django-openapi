from django_openapi_schema import *
from django_openapi_schema.constants import EMPTY


class Path(String):
    pass


class File(Schema):
    class Meta:
        data_type = "string"
        data_format = "binary"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _serialize(self, obj):
        return obj.url
