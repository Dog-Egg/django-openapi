from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin, OpenAPIConverter
from marshmallow import fields, Schema

spec = APISpec(
    title="Swagger Petstore",
    version="0.1.0",
    openapi_version="3.0.3",
    plugins=[MarshmallowPlugin()],
)


class SchemaDemo(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(description='123', metadata={"description": "The user's name"})
    created = fields.DateTime(
        # missing=datetime.datetime.now(),
        # dump_default=datetime.datetime.utcnow,
        # metadata={"default": "The current datetime"}
    )


spec.components.schema(component_id=SchemaDemo.__name__, schema=SchemaDemo)

if __name__ == '__main__':
    import pprint

    pprint.pprint(spec.to_dict())
