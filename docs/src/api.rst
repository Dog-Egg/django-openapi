API
===

Django OpenAPI
--------------

.. module:: django_openapi


.. autoclass:: OpenAPI
.. autoclass:: Resource
    :members:
.. autoclass:: Operation
    :members:


Parameter
^^^^^^^^^

.. autoclass:: django_openapi.parameter.Path
.. autoclass:: django_openapi.parameter.Query
.. autoclass:: django_openapi.parameter.Cookie
.. autoclass:: django_openapi.parameter.Header
.. autoclass:: django_openapi.parameter.Body
.. autoclass:: django_openapi.parameter.Style


Schema
------

.. module:: django_openapi.schema

.. autoclass:: Schema
    :members:

Schemas
^^^^^^^

.. autoclass:: Model
.. autoclass:: String
.. autoclass:: Integer
.. autoclass:: Float
.. autoclass:: Boolean
.. autoclass:: Date
.. autoclass:: Datetime
.. autoclass:: List
.. autoclass:: Dict
.. autoclass:: Any
.. autoclass:: AnyOf

Exceptions
^^^^^^^^^^

.. autoexception:: ValidationError


Hooks
^^^^^

.. autodecorator:: serialization_fget
.. autodecorator:: validator


Docs
-----

.. autofunction:: django_openapi.docs.swagger_ui


Utils
-----

.. autofunction:: django_openapi.utils.django.django_validator_wraps

.. autofunction:: django_openapi.utils.project.find_resources

.. |AsField| replace:: **\*仅作为字段时有效\***