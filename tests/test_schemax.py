import unittest

from openapi.schemax import fields, validators
from openapi.schemax.exceptions import DeserializationError
from openapi.schemax.fields import Schema


class Test(unittest.TestCase):
    def test_build_schema(self):
        class Schema1(Schema):
            a = fields.String()

        self.assertTrue(hasattr(Schema1, 'a'))
        self.assertFalse(hasattr(Schema1(), 'a'))

        class Schema2(Schema):
            deserialize = fields.Integer()

        # 字段和方法名冲突
        # noinspection PyCallingNonCallable
        data = Schema2().deserialize({'deserialize': '1'})
        self.assertEqual({'deserialize': 1}, data)

    def test_schema_deserialize(self):
        class Schema2(Schema):
            d = fields.Integer()

        class Schema1(Schema):
            a = fields.String()
            b = fields.Integer()
            c = Schema2()

        data = Schema1().deserialize({'a': '1', 'b': '2', 'c': {'d': '3'}})
        self.assertEqual({'a': '1', 'b': 2, 'c': {'d': 3}}, data)

    def test_validation_error(self):
        class Schema3(Schema):
            a3 = fields.Integer()

        class Schema2(Schema):
            a2 = fields.Integer()
            b2 = fields.List(fields.Integer)
            c2 = fields.List(Schema3())

        class Schema1(Schema):
            a1 = fields.Integer()
            b1 = Schema2()

        with self.assertRaises(DeserializationError):
            try:
                Schema1().deserialize({
                    'a1': 'a',
                    'b1': {
                        'a2': 'a',
                        'b2': ['1', 'a'],
                        'c2': [{'a3': 'a'}]
                    }
                })
            except DeserializationError as e:
                self.assertEqual({
                    'a1': ['不是一个整数'],
                    'b1': {
                        'a2': ['不是一个整数'],
                        'b2': {
                            1: ['不是一个整数']
                        },
                        'c2': {0: [{'a3': ['不是一个整数']}]}
                    }
                }, e.message)
                raise

    def test_list(self):
        class Schema1(Schema):
            nums = fields.List(fields.Integer)

        data = Schema1().deserialize({'nums': ['1', 2, '3']})
        self.assertEqual(data, {'nums': [1, 2, 3]})

        # 多层嵌套
        result = fields.List(fields.List(fields.Integer)).deserialize([['1', '2'], ['0']])
        self.assertEqual(result, [[1, 2], [0]])

    def test_required(self):
        class Schema1(Schema):
            a = fields.List(fields.Integer)

        result = Schema1().deserialize({})
        self.assertFalse(hasattr(result, 'a'))

        class Schema2(Schema):
            a = fields.Integer(required=True)

        with self.assertRaises(DeserializationError):
            try:
                Schema2().deserialize({})
            except DeserializationError as exc:
                self.assertEqual({'a': ['这个字段是必需的']}, exc.message)
                raise

    def test_default(self):
        with self.assertRaisesRegex(ValueError, '^不能同时定义 default 和 default_factory$'):
            fields.Integer(default=1, default_factory=lambda: None)

        class Schema1(Schema):
            a = fields.Integer(default=1)
            b = fields.Integer(default_factory=lambda: 2)

        data = Schema1().deserialize({})
        self.assertEqual({'a': 1, 'b': 2}, data)

    def test_field_name(self):
        class Schema1(Schema):
            a = fields.Integer(key='A')

        data = Schema1().deserialize({'A': '1'})
        self.assertEqual(data, {'a': 1})

    def test_string(self):
        self.assertEqual(' HELLO ', fields.String().deserialize(' HELLO '))
        self.assertEqual('HELLO', fields.String(strip=True).deserialize(' HELLO '))

    def test_validator_errors(self):
        class Schema1(Schema):
            a = fields.String(validators=[validators.Length(min=6), validators.Length(max=2)])

        with self.assertRaises(DeserializationError):
            try:
                Schema1().deserialize({'a': '123'})
            except DeserializationError as exc:
                self.assertEqual({'a': ['长度最小为 6', '长度最大为 2']}, exc.message)
                raise


if __name__ == '__main__':
    unittest.main()
