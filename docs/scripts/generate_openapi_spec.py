"""
使用 snippets/resources 中的 Resource 实例生成 OAS，放置在 swagger-ui/spec 下

可监听 snippets/resources 文件变化回调该脚本
"""
import json
import os.path
import sys
from importlib import import_module
from pkgutil import iter_modules

import django
from django.core.serializers.json import DjangoJSONEncoder

sys.path.extend([
    os.path.join(os.path.dirname(__file__), '../..'),
    os.path.normpath(os.path.join(os.path.dirname(__file__), '../snippets'))
])

from django.conf import settings

from django_openapi import OpenAPI, Resource
from django_openapi.spec.utils import Collection

settings.configure(
    INSTALLED_APPS=[
        'django.contrib.contenttypes',
        'django.contrib.auth',
    ],
    LANGUAGE_CODE='zh-Hans'
)

django.setup()

pkg = __import__('resources')

DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../swagger-ui/spec'))


def main():
    for info in iter_modules(pkg.__path__):
        if info.name.startswith('_'):
            continue
        module = import_module(pkg.__name__ + '.' + info.name)

        Collection._instances.clear()  # 由于下面的openapi 实例的 id 一样，所以导致 Collection 对象共用了，这里清空一下

        openapi = OpenAPI()
        for obj in vars(module).values():
            if isinstance(obj, Resource):
                openapi.add_resource(obj)
        spec = openapi.get_spec()
        file = os.path.join(DIR, info.name + '.json')
        with open(file, 'w') as fp:
            fp.write(json.dumps(spec, cls=DjangoJSONEncoder))
            print('Successfully generated OAS:', file)


if __name__ == '__main__':
    main()
