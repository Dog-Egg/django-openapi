请求方法
========

定义请求方法
------------

通过定义请求方法名(小写)对应的函数，可实现对应请求的处理。支持定义以下请求方法：

.. literalinclude:: ./request_method.py

.. openapiview:: ./request_method.py

在 |OAS| 中隐藏请求方法
-----------------------

使用 `Operation <django_openapi.Operation>` 装饰器，将 ``include_in_spec`` 设为 `False`。

.. literalinclude:: ./hide_request_method.py
    :emphasize-lines: 9

.. openapiview:: ./hide_request_method.py