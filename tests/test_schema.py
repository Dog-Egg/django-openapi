import re

import pytest

import django_openapi_schema as schema


def test_model_inherit():
    # 多继承同名字段继承规则应与Python成员继承规则一致
    class A(schema.Model):
        a = schema.String()

    class B(schema.Model):
        a = schema.Integer()

    class C(A, B):
        pass

    assert isinstance(C._fields["a"], schema.String)


def test_nullable():
    assert schema.String(nullable=True).serialize(None) is None
    assert schema.String(nullable=True).deserialize(None) is None

    with pytest.raises(ValueError, match="The value cannot be None."):
        schema.String().serialize(None)
    with pytest.raises(schema.ValidationError, match="['The value cannot be null.']"):
        schema.String().deserialize(None)


def test_hook__unique_within_a_single_class():
    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "The hook <('serialization_fget', 'a')> can only define one in class A, but find ['get_a', 'get_a2']."
        ),
    ):
        # 测试 serialization_fget 在单个类中只能定义一个

        class A(schema.Model):
            a = schema.String()

            @schema.serialization_fget(a)
            def get_a(self):
                ...

            @schema.serialization_fget(a)
            def get_a2(self):
                ...


def test_String__pattern():
    s = schema.String(pattern=r"^\d+$")
    assert s.deserialize("123") == "123"
    with pytest.raises(schema.ValidationError):
        try:
            s.deserialize("a123")
        except schema.ValidationError as exc:
            assert exc.format_errors() == {
                "msgs": ["'a123' does not match pattern ^\\d+$."]
            }
            raise

    # re.Pattern
    assert schema.String(pattern=re.compile(r"^\d+$")).deserialize("123") == "123"
