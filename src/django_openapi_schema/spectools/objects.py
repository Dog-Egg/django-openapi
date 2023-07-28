import typing as t

from django_openapi_schema import schemas

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


class InfoObjectSchema(schemas.Model):
    title = schemas.String()
    version = schemas.String()
    description = schemas.String(required=False)
    termsOfService = schemas.String(required=False)
    contact = schemas.Model.from_dict(
        {
            "name": schemas.String(required=False),
            "url": schemas.String(required=False),
            "email": schemas.String(required=False),
        }
    )(required=False)
    license = schemas.Model.from_dict(
        {
            "name": schemas.String(),
            "url": schemas.String(required=False),
        }
    )(required=False)


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


class OpenAPISpec:
    """OpenAPI Specification 对象"""

    def __init__(self, *, info):
        self.__paths = {}
        self.__info = InfoObjectSchema().deserialize(info)
        self.__security_schemes = {}

    @property
    def title(self):
        return self.__info["title"]

    def add_path(self, path, pathitem):
        self.__paths[path] = pathitem

    def add_security(self, data: dict):
        self.__security_schemes.update(data)

    def to_dict(self):
        return clean(
            {
                "openapi": "3.0.3",
                "info": self.__info,
                "paths": self.__paths,
                "components": {
                    "securitySchemes": self.__security_schemes,
                },
            }
        )

    def parse(self, obj, **kwargs):
        try:
            return getattr(obj, "__openapispec__")(self, **kwargs)
        except TypeError as e:
            raise RuntimeError(obj, e)
