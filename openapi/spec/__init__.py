"""
https://spec.openapis.org/oas/v3.0.3
"""
import itertools
from collections import defaultdict


class _Components:
    __components = defaultdict(lambda: defaultdict(dict))

    @classmethod
    def register(cls, *, spec_id, component_name, key, value):
        cls.__components[spec_id][component_name][key] = value

    @classmethod
    def get_components(cls, *, spec_id, namespace):
        return cls.__components[spec_id][namespace]


components = _Components()
del _Components


def default_as_none(value, default):
    if value is default:
        return None
    return value


class _ProtectedObject:
    def __init__(self, o):
        self.object = o


class _SkippedObject:
    def __init__(self, o):
        self.object = o


def protect(o):
    return _ProtectedObject(o)


def skip(o):
    return _SkippedObject(o)


def clean(spec):
    invalid_values = [None, {}, []]
    invalid = object()

    def _clean(o):
        if isinstance(o, _SkippedObject):
            return o.object

        protected = False
        if isinstance(o, _ProtectedObject):
            protected = True
            o = o.object

        if isinstance(o, dict):
            tmp = {}
            for name, value in o.items():
                value = _clean(value)
                if value is not invalid:
                    tmp[name] = value
            o = tmp
        if isinstance(o, (list, tuple, set)):
            tmp = []
            for value in o:
                value = _clean(value)
                if value is not invalid:
                    tmp.append(value)
            o = tmp

        if not protected and o in invalid_values:
            return invalid
        return o

    rv = _clean(spec)
    return rv if rv is not invalid else None


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
