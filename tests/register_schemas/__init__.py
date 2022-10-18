from django_openapi import OpenAPI
from . import schemas, views

openapi = OpenAPI(title='单独注册 Schema')
openapi.add_resource(views.API)
openapi.register_schema(schemas.SchemaA)
openapi.register_schema(schemas.SchemaB)
