from django_openapi.utils.project import find_resources


def get_openapi_from_module(module):
    """从示例模块中获取/创建 OpenAPI 实例。"""
    from django_openapi import OpenAPI

    openapi = OpenAPI()
    for r in find_resources(module):
        openapi.add_resource(r)
    return openapi
