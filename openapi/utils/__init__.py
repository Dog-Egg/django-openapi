import inspect
import itertools


def make_instance(obj):
    if inspect.isclass(obj):
        obj = obj()
    return obj


def make_schema(obj):
    from openapi.schema.schemas import Model
    if isinstance(obj, dict):
        obj = Model.from_dict(obj)
    return make_instance(obj)


def merge(obj1, obj2):
    def inner_merge(o1, o2):
        if isinstance(o1, list) and isinstance(o2, list):
            return o1 + o2
        if isinstance(o1, dict) and isinstance(o2, dict):
            o = {}
            for k in itertools.chain(o1, o2):
                if k in o1 and k in o2:
                    o[k] = merge(o1[k], o2[k])
                elif k in o1:
                    o[k] = o1[k]
                else:
                    o[k] = o2[k]
            return o
        return o2

    return inner_merge(obj1, obj2)
