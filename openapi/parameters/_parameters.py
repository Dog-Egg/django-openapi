from openapi.enums import Location
from openapi.schemax import Schema
from openapi.utils import make_schema


class _Parameters:
    location = None

    def __init__(self, schema):
        self.schema: Schema = make_schema(schema)

    def deserialize(self, params):
        return self.schema.deserialize(params)


def _parameter_cls(location=None):
    return type('Parameter', (_Parameters,), dict(location=location))


Query = _parameter_cls(Location.QUERY)
Cookie = _parameter_cls(Location.COOKIE)
Header = _parameter_cls(Location.HEADER)
Body = _parameter_cls()
