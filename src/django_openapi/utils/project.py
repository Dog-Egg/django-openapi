import typing as t

from django_openapi import Resource


def find_resources(module) -> t.Generator[Resource, None, None]:
    """查找模块内的 `Resource <django_openapi.Resource>` 对象。"""
    for value in vars(module).values():
        o = Resource.checkout(value)
        if o is not None:
            yield o
