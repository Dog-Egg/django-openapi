import pytest

from openapi.utils.enum import Enum


class Color(Enum):
    RED = 'red'
    BLUE = 'blue'
    YELLOW = 'yellow'


def test_equal():
    assert Color.RED == 'red'
    assert Color.YELLOW == 'yellow'


def test_contains():
    assert 'red' in Color


def test_not_contains():
    assert 'green' not in Color


def test_iteration():
    assert set(Color) == {'red', 'blue', 'yellow'}


def test_inherit():
    class Color2(Color):
        GREEN = 'green'

    assert Color2.RED == 'red'
    assert Color2.GREEN == 'green'
    assert set(Color2) == {'red', 'blue', 'yellow', 'green'}


def test_dont_new():
    with pytest.raises(RuntimeError, match='枚举类不可实例化'):
        Color()


def test_member_unique():
    with pytest.raises(ValueError, match='已存在'):
        class Color2(Color):
            Red = 'red'
