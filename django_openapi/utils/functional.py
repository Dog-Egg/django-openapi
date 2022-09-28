import inspect

from django_openapi.schema import schemas
from django_openapi import typing as _t


def make_instance(obj):
    if inspect.isclass(obj):
        obj = obj()
    return obj


def make_schema(obj: '_t.GeneralSchema') -> 'schemas.BaseSchema':
    if isinstance(obj, dict):
        return make_model_schema(obj)
    obj = make_instance(obj)
    if not isinstance(obj, schemas.BaseSchema):
        raise ValueError('The %r cannot be instantiated as a Schema.' % obj)
    return obj


def make_model_schema(obj: '_t.GeneralModelSchema') -> 'schemas.Model':
    if isinstance(obj, dict):
        obj = schemas.Model.from_dict(obj)
    obj = make_instance(obj)
    if not isinstance(obj, schemas.Model):
        raise ValueError('The %r cannot be instantiated as a schemas.Model.' % obj)
    return obj


def get_dict_value(o, path: str):
    for part in path.split('.'):
        if part not in o:
            return
        o = o[part]
    return o


class Filter:
    def __init__(self, include_fields=None, exclude_fields=None):
        if include_fields is not None and exclude_fields is not None:
            raise ValueError('Cannot define include_fields and exclude_fields simultaneously')
        self.include = include_fields
        self.exclude_fields = exclude_fields

    def check(self, value) -> bool:
        if self.include is not None:
            return value in self.include
        if self.exclude_fields is not None:
            return value not in self.exclude_fields
        return True
