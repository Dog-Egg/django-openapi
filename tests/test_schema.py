import datetime

from openapi.schemax import fields
from openapi.schemax.fields import Schema


def test_schema_inherit():
    """Schema 单继承"""

    class Person(Schema):
        name = fields.String()
        birthday = fields.Date()

    class Student(Person):
        grade = fields.String()

    result = Student().serialize({
        'name': '小明',
        'birthday': datetime.date(2001, 5, 1),
        'grade': '六年级'
    })
    assert result == {
        'name': '小明',
        'birthday': '2001-05-01',
        'grade': '六年级'
    }


def test_schema_multiple_inherit():
    """Schema 多继承"""

    class A(Schema):
        a = fields.Integer()
        b = fields.Integer()

    class B(Schema):
        a = fields.String()

    class C(A, B):
        b = fields.String()
        c = fields.Integer()

    result = C().serialize({'a': '1', 'b': '1', 'c': '1'})
    assert result == {'a': 1, 'b': '1', 'c': 1}
