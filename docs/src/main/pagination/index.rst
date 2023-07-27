分页
====

以下展示了 `PagePagination <django_openapi.pagination.PagePagination>` 和 `OffsetPagination <django_openapi.pagination.OffsetPagination>` 2种分页方式的用法。

.. literalinclude:: ./pagination.py
    :emphasize-lines: 16,18, 22, 24

.. note::
    使用了分页的请求方法无需为其 `Operation <django_openapi.Operation>` 定义 ``response_schema``，分页对象会将自己的响应结构设置到 Operation 中。

.. openapiview:: ./pagination.py


.. autoclass:: django_openapi.pagination.Pagination
    :members:
    :private-members:

.. autoclass:: django_openapi.pagination.PagePagination
    :show-inheritance:

.. autoclass:: django_openapi.pagination.OffsetPagination
    :show-inheritance:


自定义分页
----------

自定义分页只需继承 `Pagination <django_openapi.pagination.Pagination>`，并实现其抽象方法。

.. literalinclude:: ./pagination_customization.py

.. openapiview:: ./pagination_customization.py
    :docExpansion: full