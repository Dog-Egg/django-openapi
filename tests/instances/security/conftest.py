import pytest

from .instance import openapi


@pytest.fixture
def oas(get_oas):
    return get_oas(openapi)
