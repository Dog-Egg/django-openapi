快速开始
========

安装
----

.. code-block:: bash

    $ pip install ~/workspace/django-openapi --force


创建项目
--------

下例是由 ``django-admin`` 创建的一个项目。

.. code-block::

    mysite
    ├── manage.py
    ├── mysite
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── myapp
        ├── __init__.py
        ├── admin.py
        ├── apps.py
        ├── migrations
        │   └── __init__.py
        ├── models.py
        ├── tests.py
        └── views.py

注册应用
--------

首先需要将 ``django_openapi`` 应用添加到 Django 应用程序列表中。

.. code-block::
    :emphasize-lines: 5
    :caption: mysite/settings.py

    INSTALLED_APPS = [
        "django.contrib.admin",
        ...
        "myapp",
        "django_openapi",
    ]


编写 API
----------

然后编写如下一个简单资源 API，它像 Django 的视图函数一样，负责处理请求并返回响应。

.. literalinclude:: ./views.py
    :caption: myapp/views.py


配置路由
--------

最后将资源 API 添加到 `OpenAPI <django_openapi.OpenAPI>` 实例中，并注册其路由到 Django 路由配置中。

.. code-block::
    :caption: mysite/urls.py

    from django.contrib import admin
    from django.urls import include, path
    from django_openapi import OpenAPI
    from django_openapi.docs import swagger_ui

    from myapp import views

    openapi = OpenAPI()
    openapi.add_resource(views.GreetingAPI)

    urlpatterns = [
        path("admin/", admin.site.urls),
        path("", include(openapi.urls)),
        path("docs/", swagger_ui(openapi))  # 这里使用 SwaggerUI 用来查看 API 文档
    ]


查看文档
--------

使用下面命令启动 Django 开发服务器

.. code-block:: bash

    $ python manage.py runserver

并访问 http://localhost:8000/docs/，将看到如下的文档页面。

.. openapiview:: ./views.py