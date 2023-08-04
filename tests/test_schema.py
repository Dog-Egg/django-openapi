import re
from datetime import datetime, timedelta, timezone

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
        (schema.Float(), ".2", 0.2),
        (schema.Datetime(), datetime(2000, 1, 1), "2000-01-01T00:00:00"),
        (
            schema.Datetime(),
            datetime(2000, 1, 1, tzinfo=timezone(timedelta(hours=8))),
            "2000-01-01T00:00:00+08:00",
        ),
    ],
)
def test_serialize(schemaobj, input, output):
    result = schemaobj.serialize(input)
    assert result == output
    assert type(result) is type(output)


@pytest.mark.parametrize(
    "schemaobj, input, output",
    [
        (schema.Integer(), "1.0", 1),
        (schema.Integer(), "1", 1),
        (schema.Integer(), 1, 1),
        (schema.Float(), ".2", 0.2),
        (schema.Datetime(), "2022-01-01 08:00", datetime(2022, 1, 1, 8)),
        (
            schema.Datetime(),
            "2022-01-01 07:00+08:00",
            datetime(2022, 1, 1, 7, tzinfo=timezone(timedelta(hours=8))),
        ),
    ],
)
def test_deserialize(schemaobj, input, output):
    result = schemaobj.deserialize(input)
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
        (schema.Float(), {}, [{"msgs": ["Deserialization failure."]}]),
        (schema.Integer(), "1.1", [{"msgs": ["Not a valid integer."]}]),
        (
            schema.Datetime(with_tz=True),
            "2022-01-01 08:00",
            [{"msgs": ["Not support timezone-naive datetime."]}],
        ),
        (
            schema.Datetime(with_tz=False),
            "2022-01-01 08:00+08:00",
            [{"msgs": ["Not support timezone-aware datetime."]}],
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


def test_Password_clear_value():
    class User(schema.Model):
        password = schema.Password()  # Password 仅判断空字符串为无效值

    assert User().deserialize({"password": " "}) == {"password": " "}
    with pytest.raises(schema.ValidationError):
        try:
            User().deserialize({"password": ""})
        except schema.ValidationError as e:
            assert e.format_errors() == [
                {"msgs": ["This field is required."], "loc": ["password"]}
            ]
            raise
