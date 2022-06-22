import unittest

from openapi.operation import Operation
from openapi.parameters import Parameter
from openapi.schema import properties


class TestSchema(unittest.TestCase):
    def test_deserialize(self):
        class Schema1(properties.Schema):
            class Schema2(properties.Schema):
                c = properties.Integer()

            a = properties.String()
            b = properties.Integer()
            obj2 = Schema2()

        schema = Schema1().deserialize({'a': 1, 'b': '2', 'obj2': {'c': '2'}})
        self.assertEqual(schema.a, '1')
        self.assertEqual(schema.b, 2)
        self.assertEqual(schema.obj2.c, 2)

    def test_from_dict(self):
        schema_cls = properties.Schema.from_dict({'a': properties.Integer()})
        result = schema_cls().deserialize({'a': '1'})
        self.assertEqual(result.a, 1)


class TestOperation(unittest.TestCase):
    def test(self):
        operation = Operation(
            parameters=[
                Parameter(properties.Integer())
            ]
        )
