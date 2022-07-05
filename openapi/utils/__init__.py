import inspect


def make_instance(obj):
    if inspect.isclass(obj):
        obj = obj()
    return obj


def make_schema(obj):
    from openapi.schemax import Schema
    if isinstance(obj, dict):
        obj = Schema.from_dict(obj)
    return make_instance(obj)
