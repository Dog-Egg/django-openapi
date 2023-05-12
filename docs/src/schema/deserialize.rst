反序列化
========


数字
----

如 `Integer <django_openapi.schema.Integer>`, `Float <django_openapi.schema.Float>` 类具有以下功能。


数值范围限制
^^^^^^^^^^^^

参数 ``gt`` (大于)， ``gte`` (大于或等于)， ``lt`` (小于)， ``lte`` (小于或等于) 用于限制反序列数值大小。

.. code-block::

    >>> from django_openapi import schema

    >>> schema.Integer(gt=1).deserialize(8) # 限制数值大于 1
    8

    >>> schema.Integer(gt=1).deserialize(0) # 限制数值大于 1
    Traceback (most recent call last):
        ...
    django_openapi_schema.exceptions.ValidationError: {'msgs': ['The value must be greater than 1.']}


倍数限制
^^^^^^^^

参数 ``multiple_of`` 用于设置反序列数值的整数倍。

.. code-block::

    >>> price = schema.Float(gte=0, multiple_of=0.01) # 如校验一个有效的价格

    >>> price.deserialize(1.51)
    1.51

    >>> price.deserialize(1.505)
    Traceback (most recent call last):
        ...
    django_openapi_schema.exceptions.ValidationError: {'msgs': ['The value must be a multiple of 0.01.']}