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
            assert exc.format_errors() == [
                {"msgs": ["'a123' does not match pattern ^\\d+$."]}
            ]
            raise

    # re.Pattern
    assert schema.String(pattern=re.compile(r"^\d+$")).deserialize("123") == "123"


def test_ValiationError():
    with pytest.raises(schema.ValidationError):
        try:
            schema.List(schema.String(min_length=3, pattern=r"\d+")).deserialize(
                ["123", "ab"]
            )
        except schema.ValidationError as e:
            assert e.format_errors() == [
                {
                    "msgs": [
                        "'ab' does not match pattern \\d+.",
                        "The length must be greater than or equal to 3.",
                    ],
                    "loc": [1],
                }
            ]
            raise


@pytest.mark.parametrize(
    "schemaobj, input, output",
    [
        (schema.Float(), "0", 0.0),
    ],
)
def test_serialize(schemaobj, input, output):
    result = schemaobj.serialize(input)
    assert result == output
    assert type(result) is type(output)


@pytest.mark.parametrize(
    "schemaobj, input, err",
    [
        (schema.Integer(), "a", [{"msgs": ["Not a valid integer."]}]),
        (
            schema.Dict(schema.Integer),
            {"a": 1, "b": "b"},
            [{"msgs": ["Not a valid integer."], "loc": ["b"]}],
        ),
    ],
)
def test_deserialize_error(schemaobj, input, err):
    with pytest.raises(schema.ValidationError):
        try:
            schemaobj.deserialize(input)
        except schema.ValidationError as e:
            assert e.format_errors() == err
            raise e


def test_ValidationError_error_messages():
    e1 = schema.ValidationError()
    e2 = schema.ValidationError(key="required")

    e3 = schema.ValidationError(key="required")
    e3.update_error_message({"required": "这个值是必须的。"})

    e4 = schema.ValidationError("发生了一些错误")

    e1.setitem_error("e2", e2)
    e1.setitem_error("e3", e3)
    e1.setitem_error("e4", e4)

    assert e1.format_errors() == [
        {"loc": ["e2"], "msgs": ["This field is required."]},
        {"loc": ["e3"], "msgs": ["这个值是必须的。"]},
        {"loc": ["e4"], "msgs": ["发生了一些错误"]},
    ]
