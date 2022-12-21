API
===

.. autoclass:: django_openapi.OpenAPI
    :members:  urls, add_resource, register_schema
.. autoclass:: django_openapi.Resource
.. autoclass:: django_openapi.Operation
.. autoclass:: django_openapi.Respond
    :members:

Parameter
#########
.. automodule:: django_openapi.parameters
    :members: Query, Cookie, Header, Body

Schema
######
.. autoclass:: django_openapi.schema.schemas.BaseSchema
    :members: Meta
.. autoclass:: django_openapi.schema.schemas.String
.. autoclass:: django_openapi.schema.schemas.Model

Specification
#############
.. automodule:: django_openapi.spec
    :members: Tag, ExternalDocs, Example
