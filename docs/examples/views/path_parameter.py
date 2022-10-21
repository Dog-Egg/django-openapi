from django_openapi import Resource


# 使用 `{}` 括号声明一个路径参数
# highlight-next-line
@Resource('/path/{id}')
class API:
    # 路径参数以关键字参数的形式传递给 `class API`
    # highlight-next-line
    def __init__(self, request, id):
        pass

    def get(self):
        pass
