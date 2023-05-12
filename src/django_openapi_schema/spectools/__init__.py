import inspect
import typing as t


class OpenAPISpec:
    """OpenAPI Specification 对象"""

    def __init__(self, *, title="API Document", version: str = "0.1.0"):
        self._title = title
        self._paths = {}
        self._version = version

    def add_path(self, path, obj):
        self._paths[path] = self.parse(obj)

    def to_dict(self):
        return clean(
            {
                "openapi": "3.0.3",
                "info": {
                    "title": self._title,
                    "version": self._version,
                },
                "paths": self._paths,
            }
        )

    def parse(self, obj, **kwargs):
        return getattr(obj, "__openapispec__")(self, **kwargs)


_CLEARN_INVALID_VALUES = [None, {}, []]


T = t.TypeVar("T")


class Protect(t.Generic[T]):
    """保护最外层无效值不被 `clean` 清除。

    >>> clean({'schema': Protect({'type': None})})
    {'schema': {}}
    """

    def __init__(self, obj: T) -> None:
        self._obj = obj

    def __call__(self) -> T:
        return self._obj


def clean(data: T) -> T:
    """
    >>> clean([{}, 0, None, [None], 1])
    [0, 1]
    """

    if isinstance(data, dict):
        new = type(data)()
        for name, value in data.copy().items():
            protected = isinstance(value, Protect)
            if protected:
                value = value()
            value = clean(value)
            if protected or value not in _CLEARN_INVALID_VALUES:
                new[name] = value
        return new

    elif isinstance(data, list):
        new = type(data)()
        for value in data:
            protected = isinstance(value, Protect)
            if protected:
                value = value()
            value = clean(value)
            if protected or value not in _CLEARN_INVALID_VALUES:
                new.append(value)
        return new

    return data


def default_as_none(value, default):
    if value is default:
        return None
    return value


def clean_commonmark(text: str):
    if not text:
        return None
    return inspect.cleandoc(text)
