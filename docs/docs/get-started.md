# 开始

假设你已经通过 [Django 教程](https://docs.djangoproject.com/zh-hans/4.0/intro/tutorial01/) 创建了一个 polls 应用

## 设置

将 django-openapi 添加到 `INSTALLED_APPS` 中

```python title="mysite/settings.py"
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # highlight-next-line
    'openapi'
]
```

## 创建一个 Resource

`QuestionAPI` 只是一个普通的类，需要用 `@Resource` 标记为一个请求资源，`get` 方法负责处理 GET 请求

```python title="polls/views.py"
from openapi import Resource


@Resource('/questions')
class QuestionAPI:
    def get(self, request):
        return 'ok'
```

## 添加到 Django 路由

```python title="polls/urls.py"
from django.urls import path, include

from openapi import OpenAPI
from . import views

# highlight-start
openapi = OpenAPI(__name__, enable_swagger_ui=True)
openapi.find_resources(views)
# highlight-end

urlpatterns = [
    path('', include(openapi.urls))
]
```

## 查看 API 文档

运行项目然后访问 http://127.0.0.1:8000/polls/swagger-ui

```bash
python manage.py runserver
```

<BrowserWindow url={"http://127.0.0.1:8000/polls/swagger-ui"}>
<img src={require("./screenshots/get-started-1.png").default} />
</BrowserWindow>
