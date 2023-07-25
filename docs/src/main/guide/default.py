from datetime import datetime

from django_openapi import Resource, schema
from django_openapi.parameter import Query


@Resource("/to/path")
class API:
    def get(
        self,
        query=Query(
            {
                "a": schema.String(default="Hello World"),
                "b": schema.Datetime(default=lambda: datetime.now()),  # 使用函数定义动态默认值
            }
        ),
    ):
        ...
