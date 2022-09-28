from urllib.parse import urljoin

from django_openapi import OpenAPI
from . import views


class MyOpenAPI(OpenAPI):
    def get_spec(self, request=None):
        spec = super().get_spec(request)
        for s in spec['servers']:
            s['url'] = urljoin('https://example.com', s['url'])
            s['description'] = '测试服务器'
        return spec


openapi = MyOpenAPI(title='Specification Testing')

openapi.add_resource(views.A)
