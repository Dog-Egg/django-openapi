请求权限
========

`Resource <django_openapi.Resource>` 和 `Operation <django_openapi.Operation>` 都有一个 ``permission`` 参数，用于设置请求权限。

如下示例接口要求具有"管理员权限"的用户才可访问。

.. literalinclude:: ./example.py
    :emphasize-lines:
.. openapiview:: ./example.py

.. note::
    如果 `Resource <django_openapi.Resource>` 和 `Operation <django_openapi.Operation>` 都设置 permission，则需要请求同时拥有两者的权限，相关内容查看 :ref:`permission-combination`。


.. automodule:: django_openapi.permissions
    :members:


.. _permission-combination:

权限组合
--------

权限之间可以实现“与”、“或”的逻辑运算。

使用 ``&`` 操作符表示 "与" 运算，使用 ``|`` 操作符表示 "或" 运算。

.. warning::
    不支持 "非" 运算。

如下示例为 2 个权限组合为 "与" 关系。

.. testcode::

    from django_openapi.permissions import IsAdministrator, HasPermission

    permission = IsAdministrator & HasPermission("polls.create_poll")
    # 组合产生的 permission 表示请求用户必需是管理员，且拥有 "polls.create_poll" 权限。