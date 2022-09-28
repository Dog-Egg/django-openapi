from django_openapi.schema import schemas


def test_fallback():
    def id_fallback(value):
        return int(value)

    def field_fallback(_):
        return 123

    class FooSchema(schemas.Model):
        id = schemas.Integer(read_only=True, required=True, fallback=id_fallback)
        field = schemas.Integer(fallback=field_fallback, required=True)

    assert FooSchema().serialize({'id': '1'}) == {'id': 1, 'field': 123}
