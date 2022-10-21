---
sidebar_position: 2
---

# 开始

## 安装

由于当前还在测试阶段，所以没有上传到 pypi，这里提供从 git 仓库的安装方法。

```bash
pip install git+https://github.com/Dog-Egg/django-openapi.git@0.1a3
```

## 添加到 Django 项目中

将 django_openapi 添加到 `INSTALLED_APPS` 中

```python title="settings.py"
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # highlight-next-line
    'django_openapi',
    # ...
]
```

## 使用

写一个最简单的例子，我们直接在项目目录的 `urls.py` 文件内编写代码。

```python
from django.urls import path, include
from django_openapi import Resource, OpenAPI
from django_openapi.docs import swagger_ui


@Resource('/path')
class API:
    def get(self):
        pass


openapi = OpenAPI()
openapi.add_resource(API)

urlpatterns = [
    # ...
    path('api/', include(openapi.urls)),  # 请注意这里需要使用 `include` 函数
    path('docs/', swagger_ui(openapi)),
]
```

### 查看 API 文档

运行项目然后访问 http://127.0.0.1:8000/docs/

<SwaggerUI spec="开始" height={430}></SwaggerUI>

### 视图

django-openapi 的核心是提供了一种新的"视图"编写方式。

```python
from django_openapi import Resource, Operation


@Resource('/path')  # ①
class API:
    # def __init__(self, request):  # ②
    #    self.request = request

    @Operation(summary='这是一个GET请求方法')  # ③
    def get(self):  # ④
        # 编写请求处理代码
        return 'ok'  # ⑤
```

- ① `Resource` 用于提供请求路径等，并将装饰的类标记为一个资源，资源最终会被 OpenAPI 对象转为视图函数；
- ② `__init__` 函数并非必须定义的，当你需要 `request` 对象或其他路径参数时，可定义 `__init__` 函数来获取；
- ③ `Operation` 为装饰的请求方法提供额外的接口描述和功能；
- ④ 定义 `get` 方法表示该路由可以处理 HTTP GET 请求，也可定义 `post`, `put`, `delete` 等方法来实现对应的请求处理；
- ⑤ 请求方法并非必须返回一个 `response` 对象，通过自定义 [Respond](./respond)，你可以返回任何你喜欢的数据类型和值；