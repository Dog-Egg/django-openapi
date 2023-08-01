反序列化
========


倍数限制
^^^^^^^^

参数 ``multiple_of`` 用于设置反序列数值的整数倍。

.. code-block::

    >>> from django_openapi import schema

    >>> price = schema.Float(minimum=0, multiple_of=0.01) # 如校验一个有效的价格

    >>> price.deserialize(1.51)
    1.51

    >>> price.deserialize(1.505)
    Traceback (most recent call last):
        ...
    django_openapi_schema.exceptions.ValidationError: [{'msgs': ['The value must be a multiple of 0.01.']}]