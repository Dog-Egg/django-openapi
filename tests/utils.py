import hashlib
import inspect
import os
import sys
from importlib import import_module
from pkgutil import walk_packages

from django_openapi import Resource, OpenAPI
from django_openapi.spec import Tag, ExternalDocs


def _build_tag():
    dirname = os.path.dirname(os.path.dirname(__file__))
    # noinspection PyUnresolvedReferences,PyProtectedMember
    frame = inspect.getframeinfo(sys._getframe(3))
    filepath = os.path.relpath(frame.filename, dirname)

    for name, module in sys.modules.items():
        if getattr(module, '__file__', None) == frame.filename:
            doc = inspect.getdoc(module)
            name = doc if doc else filepath
            description = f'_{filepath}_' if doc else None
            return Tag(
                name=name,
                description=description,
                external_docs=ExternalDocs(getattr(module, '__url__', None))
            )

    return filepath


def _build_path():
    # noinspection PyUnresolvedReferences,PyProtectedMember
    frame = inspect.getframeinfo(sys._getframe(3))
    return '/' + hashlib.md5(('%s:%s' % (frame.filename, frame.lineno)).encode()).hexdigest()[:8]


class _TestResource(Resource):
    def __init__(self, path=None, **kwargs):
        if path is None:
            path = _build_path()
        self.__path = path
        kwargs.setdefault('tags', [_build_tag()])
        super().__init__(path, **kwargs)


# noinspection PyPep8Naming
def TestResource(*args, **kwargs) -> _TestResource:
    if args and callable(args[0]):
        return _TestResource()(args[0])  # type: ignore
    return _TestResource(*args, **kwargs)


class ResourceView:
    def __init__(self, request, **kwargs):
        self.request = request
        self.pathargs = kwargs


def itemgetter(o, path):
    if isinstance(path, str):
        path = path.split('.')

    for part in path:
        o = o[part]
    return o


class TestOpenAPI(OpenAPI):
    def find_resources(self, package):
        package = import_module(package)
        for info in walk_packages(package.__path__):
            module = import_module(package.__name__ + '.' + info.name)
            for v in vars(module).values():
                if Resource.checkout(v):
                    self.add_resource(v)
