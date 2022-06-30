from collections import defaultdict

__all__ = ['components']


class Components:
    def __init__(self):
        self._schemas = defaultdict(dict)

    def register_schema(self, spec_id, *, name, schema):
        self._schemas[spec_id][name] = schema

    def get_schemas(self, spec_id):
        return self._schemas[spec_id]


components = Components()
del Components
