from tests.utils import itemgetter
from . import openapi


def test_oas(get_oas):
    oas = get_oas(openapi)
    assert 'security' not in itemgetter(oas, 'paths./.get')

    assert itemgetter(oas, 'paths./.post.security') == [{'from': []}, {'token': []}]

    assert itemgetter(oas, 'paths./.put.security') == []
