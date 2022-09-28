"""
https://spec.openapis.org/oas/v3.0.3
"""
import inspect
import itertools
import typing

from django_openapi import spec


class Collection:
    _instances: typing.Dict[str, 'Collection'] = {}
    security: list
    schemas: dict

    class _TagsCollection:
        def __init__(self):
            self._tags: typing.Dict[str, 'spec.Tag'] = {}

        def add(self, tag: 'spec.Tag'):
            if tag.name in self._tags and self._tags[tag.name] != tag:
                raise ValueError('The tag %s already exists.' % tag)
            self._tags[tag.name] = tag

        def list(self) -> typing.List[dict]:
            return list(self._tags.values())

    tags: _TagsCollection

    def __new__(cls, spec_id: str):
        assert isinstance(spec_id, str)
        if spec_id not in cls._instances:
            self = super().__new__(cls)
            cls._instances[spec_id] = self

            self.schemas = {}
            self.security = []
            self.tags = cls._TagsCollection()

        return cls._instances[spec_id]


def default_as_none(value, default):
    if value is default:
        return None
    return value


class _SpecialObject:
    def __init__(self, obj, *args, **kwargs):
        self._obj = obj
        self._args = args
        self._kwargs = kwargs

    def clean(self):
        if callable(self._obj):
            return self._obj(*self._args, **self._kwargs)
        return self._obj


class Protect(_SpecialObject):
    pass


class Skip(_SpecialObject):
    pass


def clean(spec):
    invalid_values = [None, {}, []]
    invalid = object()

    def _clean(o):
        if isinstance(o, Skip):
            return o.clean()

        protected = False
        if isinstance(o, Protect):
            protected = True
            o = o.clean()

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


def clean_commonmark(content: typing.Optional[str]):
    if not content:
        return
    return inspect.cleandoc(content)
