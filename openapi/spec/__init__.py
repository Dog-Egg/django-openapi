"""
https://spec.openapis.org/oas/v3.0.3
"""

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


def protect(data):
    class Protected(type(data)):
        _protected_ = True

    return Protected(data)


def clean(spec):
    def _clean(data):
        protected = hasattr(data, '_protected_')
        if isinstance(data, dict):
            d = {}
            for name, value in data.items():
                value = _clean(value)
                if value is not None:
                    d[name] = value
            data = d
        if isinstance(data, list):
            d = []
            for value in data:
                value = _clean(value)
                if value is not None:
                    d.append(value)
            data = d

        if protected:
            return data
        return data or None

    return _clean(spec)
