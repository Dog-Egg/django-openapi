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

内置异常
--------

.. automodule:: django_openapi.exceptions
    :members: