请求对象
========

只有定义了 ``__init__`` 方法的 Resource 装饰类才会接收到请求对象，该请求对象为 Django 的 `HttpRequest <https://docs.djangoproject.com/en/4.2/ref/request-response/#httprequest-objects>`_。

.. literalinclude:: ./request_object.py