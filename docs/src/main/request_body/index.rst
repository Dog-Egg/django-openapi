请求体
======

同时支持 JSON 和 表单
---------------------

如果需要请求体同时支持 JSON 和 表单格式。可以将 ``content_type`` 设为列表，并写入 ``multipart/form-data`` 和 ``application/json``。

.. literalinclude:: ./multiple_content_types.py
.. openapiview:: ./multiple_content_types.py
    :docexpansion: full