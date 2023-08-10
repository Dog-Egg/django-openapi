异常处理
========

异常处理旨在处理请求函数中抛出的异常，并返回响应。

使用示例
--------

.. testcode::

    from django_openapi import OpenAPI
    from django.http import HttpResponse

    class MyError(Exception):
        pass

    openapi = OpenAPI()

    @openapi.error_handler(MyError)
    def handle_my_error(exc, request):
        # 当请求函数中抛出 MyError 异常时，将被该函数处理。
        return HttpResponse('A sentence...')

    @openapi.error_handler(Exception)
    def handle_other_exceptions(exc, request):
        # 监听 Exception，则其它未被捕获的异常都将通过该函数。
        return HttpResponse("内部错误", status=500)

.. warning::
    "异常处理" 的过程实际是在 Resource 视图内部运行的，所以会导致像 Django `ATOMIC_REQUESTS <https://docs.djangoproject.com/zh-hans/4.2/ref/settings/#atomic-requests>`_ 功能无法如预期运行。

    ATOMIC_REQUESTS 是将视图包裹在数据库的事务中，当视图抛出异常时，则会执行回滚。所以有时会出现部分异常先被 "异常处理" 捕获，导致外部包裹数据库事务无法预期捕获异常执行回滚。

    但这并不构成问题，可以显示控制事务，只是需要在编码中注意这一点。

内置异常
--------

.. automodule:: django_openapi.exceptions
    :members: