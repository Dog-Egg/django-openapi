from django_openapi import Resource, schema
from django_openapi.parameter import Path, Style


@Resource(
    Path(
        "/color/{color}",
        param_schemas={"color": schema.List()},
        param_styles={"color": Style("simple", False)},  # 这是 path 参数默认的样式
    )
)
class API:
    def __init__(self, request, color):
        ...

    def get(self):
        ...
