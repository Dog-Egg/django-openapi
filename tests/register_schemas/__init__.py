from django_openapi import OpenAPI
from django_openapi.schema import schemas


class SchemaA(schemas.Model):
    """
    结构表述
    """
    a = schemas.String()
    b = schemas.Integer()


SchemaB = schemas.Model.from_dict(dict(
    a=schemas.Integer(),
    b=schemas.List(),
))

openapi = OpenAPI(title='单独注册 Schema')
openapi.register_schema(SchemaA)
openapi.register_schema(SchemaB)
