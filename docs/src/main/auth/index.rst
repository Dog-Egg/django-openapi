用户认证与鉴权
==============

使用 `Operation <django_openapi.Operation>` 的 ``auth`` 参数来设置请求认证。

如下示例接口只有"管理员"用户才可访问。

.. literalinclude:: ./example.py
    :emphasize-lines: 7
.. openapiview:: ./example.py

也可以使用 `Resource <django_openapi.Resource>` 的 ``default_auth`` 参数为其下所有的 Operation 提供默认的 auth。

.. warning::
    以下认证类基于 `django.contrib.auth <https://docs.djangoproject.com/en/4.2/ref/contrib/auth/>`_ 应用实现。如需使用，请确定你的 API 用户验证系统基于 django.contrib.auth 应用。

.. automodule:: django_openapi.auth
    :members: IsAuthenticated, IsAdministrator, IsSuperuser, HasPermission


自定义认证
-----------

如果你的项目单独开发了一套用户系统，可参考以下代码自定义用户认证。


.. literalinclude:: ./custom.py
.. openapiview:: ./custom.py

.. autoclass:: django_openapi.auth.BaseAuth
    :members: