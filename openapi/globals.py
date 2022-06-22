from openapi.spec.schema import OpenAPIObject, InfoObject, PathsObject, ServerObject

openapi = OpenAPIObject(
    info=InfoObject(title='This is Title'),
    paths=PathsObject({}),
    servers=[ServerObject(url='/api')]
)
