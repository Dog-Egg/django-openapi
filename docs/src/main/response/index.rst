响应
====

声明响应结构
------------

使用 `Operation <django_openapi.Operation>` 的 ``response_schema`` 参数声明响应结构。

.. literalinclude:: ./response_schema.py

.. openapiview:: ./response_schema.py
    :docExpansion: full


返回响应(待完善)
-----------------

Django 的视图函数要求返回一个 `HttpResponse <https://docs.djangoproject.com/en/4.2/ref/request-response/#django.http.HttpResponse>`_
对象，所以 Django OpenAPI 的请求函数返回值都会通过一个 ``make_response`` 函数，它的源码如下。
