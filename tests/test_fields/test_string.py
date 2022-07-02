import pytest

from openapi.schemax.exceptions import SerializationError, DeserializationError
from openapi.schemax.fields import String


def test_serialize():
    assert String().serialize('1') == '1'

    with pytest.raises(SerializationError, match='必须是字符串'):
        String().serialize(1)


def test_deserializer():
    assert String().deserialize('1') == '1'

    with pytest.raises(DeserializationError, match='必须是字符串'):
        assert String().deserialize(1) == '1'


def test_strip():
    assert String(strip=False).serialize(' a') == ' a'
    assert String(strip=True).serialize(' a') == ' a'
    assert String(strip=True).deserialize(' a') == 'a'
    assert String(strip=False).deserialize(' a') == ' a'
