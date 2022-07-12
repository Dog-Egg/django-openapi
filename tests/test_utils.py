from openapi.utils import merge


def test_merger():
    assert merge({'a': [1, 2], 'b': {'c': 1}}, {'a': [3]}) == {'a': [1, 2, 3], 'b': {'c': 1}}
    assert merge({'a': {'b': [1]}}, {'a': {'b': [2]}}) == {'a': {'b': [1, 2]}}
    assert merge({'a': {'b': 1}}, {'a': {'b': 2}}) == {'a': {'b': 2}}
