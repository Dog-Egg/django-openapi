from django_openapi import Operation, Resource, schema


class ResponseSchema(schema.Model):
    code = schema.Integer()
    message = schema.String()


@Resource("/to/path")
class API:
    @Operation(response_schema=ResponseSchema)
    def get(self):
        ...
