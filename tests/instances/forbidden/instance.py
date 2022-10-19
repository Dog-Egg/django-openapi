from django.http import HttpResponse

from django_openapi import OpenAPI


class MyOpenAPI(OpenAPI):
    """测试 apispec 接口权限"""

    def spec_view(self, request):
        return HttpResponse(status=403)


openapi = MyOpenAPI(title='[测试]禁止访问的文档')
