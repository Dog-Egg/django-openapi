import unittest
from dataclasses import dataclass

from openapi.schemax import fields
from openapi.schemax.fields import Schema


class TestSerialize(unittest.TestCase):
    def test_serialize(self):
        class Schema1(Schema):
            a = fields.Integer()
            b = fields.String()

        self.assertEqual({'a': 1, 'b': '1'}, Schema1().serialize({'a': 1, 'b': 1}))

        @dataclass
        class Data:
            a: int
            b: int

        self.assertEqual({'a': 1, 'b': '1'}, Schema1().serialize(Data(a=1, b=1)))
