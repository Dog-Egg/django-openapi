import importlib
import inspect
import operator
from typing import Mapping

from .. import schema


def make_instance(obj):
    if inspect.isclass(obj):
        obj = obj()
    return obj


def make_schema(obj) -> schema.Schema:
    if isinstance(obj, dict):
        return make_model_schema(obj)
    obj = make_instance(obj)
    if not isinstance(obj, schema.Schema):
        raise ValueError("The %r cannot be instantiated as a Schema." % obj)
    return obj


def make_model_schema(obj) -> schema.Model:
    if isinstance(obj, dict):
        obj = schema.Model.from_dict(obj)
    obj = make_instance(obj)
    if not isinstance(obj, schema.Model):
        raise ValueError("The %r cannot be instantiated as a schemas.Model." % obj)
    return obj


def get_dict_value(o, path: str):
    for part in path.split("."):
        if part not in o:
            return
        o = o[part]
    return o


class Filter:
    def __init__(self, include_fields=None, exclude_fields=None):
        if include_fields is not None and exclude_fields is not None:
            raise ValueError(
                "Cannot define include_fields and exclude_fields simultaneously"
            )
        self.include = include_fields
        self.exclude_fields = exclude_fields

    def check(self, value) -> bool:
        if self.include is not None:
            return value in self.include
        if self.exclude_fields is not None:
            return value not in self.exclude_fields
        return True


class Getter:
    EXCEPTIONS = (AttributeError, KeyError)

    def __init__(self, obj):
        self.obj = obj
        self.getter = operator.getitem if isinstance(obj, Mapping) else getattr

    def __call__(self, name):
        return self.getter(self.obj, name)


def import_string(obj_path: str, default_module: str = ""):
    if ":" in obj_path:
        module, obj = obj_path.rsplit(":", 1)
    elif "." in obj_path:
        module, obj = obj_path.rsplit(".", 1)
    else:
        module, obj = None, obj_path

    module = module or default_module

    return operator.attrgetter(obj)(importlib.import_module(module))
