文件上传
========

需要将 Content-Type 设为 ``multipart/form-data``。

.. literalinclude:: ./upload.py
    :emphasize-lines: 13
.. openapiview:: ./upload.py


上传多个文件
------------

.. literalinclude:: ./upload_multiple_files.py
    :emphasize-lines: 11
.. openapiview:: ./upload_multiple_files.py


验证上传的图片
---------------

这里使用 `Pillow <https://pypi.org/project/Pillow/>`_ 库来验证图片。

.. literalinclude:: ./upload_image.py
