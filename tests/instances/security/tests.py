from tests.utils import itemgetter


def test_oas(oas):
    assert 'security' not in itemgetter(oas, 'paths./.get')

    assert itemgetter(oas, 'paths./.post.security') == [{'from': []}, {'token': []}]

    assert itemgetter(oas, 'paths./.put.security') == []
