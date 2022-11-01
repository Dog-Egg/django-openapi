from urllib.parse import urljoin

from ...utils import TestOpenAPI


class MyOpenAPI(TestOpenAPI):
    def get_spec(self, request=None):
        spec = super().get_spec(request)
        for s in spec['servers']:
            s['url'] = urljoin('https://example.com', s['url'])
            s['description'] = '测试服务器'
        return spec


openapi = MyOpenAPI(title='Specification Testing')

openapi.find_resources(__package__)

__prefix__ = 'spec'
