import inspect


def make_instance(obj):
    if inspect.isclass(obj):
        obj = obj()
    return obj


def make_schema(obj):
    from openapi.schema.schemas import Model
    if isinstance(obj, dict):
        obj = Model.from_dict(obj)
    return make_instance(obj)
