import importlib
from pkgutil import iter_modules

from django.urls import path, include

from django_openapi import OpenAPI
from django_openapi.docs import swagger_ui


def find_openapi_instances():
    from tests import instances
    rv = []
    for info in iter_modules(instances.__path__):
        if not info.ispkg:
            continue

        module = importlib.import_module('%s.%s.instance' % (instances.__name__, info.name))

        prefix = getattr(module, '__prefix__', info.name)
        if prefix:
            prefix += '/'

        for v in vars(module).values():
            if isinstance(v, OpenAPI):
                rv.append((prefix, v))
                break
        else:
            raise RuntimeError(f'没有在{module}中发现 OpenAPI 实例')
    return rv


instances = find_openapi_instances()


def build_urls():
    urls = [
        path('', swagger_ui(*dict(instances).values(), load_local_static=True), name='index'),
    ]
    for prefix, instance in instances:
        urls.append(
            path(prefix, include(instance.urls)),
        )
    return urls


urlpatterns = build_urls()
