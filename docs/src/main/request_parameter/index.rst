请求参数
========


Path 参数
----------

使用 OAS `路径模板 <https://spec.openapis.org/oas/v3.0.3#path-templating>`_ 指定路径参数。

.. literalinclude:: ./path_param.py
    :emphasize-lines: 4

.. note::
    路径参数的请求实参需要定义 ``__init__`` 方法来接收。

.. openapiview:: ./path_param.py
    :docexpansion: full

指定路径参数结构
^^^^^^^^^^^^^^^^^

使用 `Path <django_openapi.parameter.Path>` 定义路径及路径参数结构。

.. literalinclude:: ./path_param2.py
    :emphasize-lines: 6-9

.. openapiview:: ./path_param2.py
    :docexpansion: full


Query 参数
--------------

.. literalinclude:: ./query_param.py
    :emphasize-lines: 13

.. openapiview:: ./query_param.py
    :docexpansion: full


Header 参数
----------------

.. literalinclude:: ./header_param.py

.. openapiview:: ./header_param.py
    :docexpansion: full


Cookie 参数
-----------------

.. literalinclude:: ./cookie_param.py

.. openapiview:: ./cookie_param.py
    :docexpansion: full


参数样式
--------

.. module:: django_openapi.parameter

支持 OAS 定义的 `参数样式 <https://spec.openapis.org/oas/v3.0.3#style-values>`_，可使用 `Style <django_openapi.parameter.Style>` 为参数指定样式。

----

下例是为 `Path` 的数组类型参数 ``color`` 指定样式 ``style: simple, explode: false`` (默认)。如果请求路径为 ``/color/red,blue,yellow`` ，则 ``__init__`` 方法接收到的 ``color`` 值为 ``['red', 'blue', 'yellow']`` 。

.. literalinclude:: ./path_style.py
    :emphasize-lines: 9

.. openapiview:: ./path_style.py

----

`Query`, `Header` 和 `Cookie` 使用相同的方式指定参数样式。如下例，query 请求参数将形如 ``color[R]=100&color[G]=200&color[B]=150``。

.. literalinclude:: ./query_style.py
    :emphasize-lines: 17

.. openapiview:: ./query_style.py
