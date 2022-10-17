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
