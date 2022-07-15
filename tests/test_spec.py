from openapi import spec


def test_spec_clean():
    assert spec.clean({'schemas': ['name1', None]}) == {'schemas': ['name1']}
    assert spec.clean({'schemas': [None, None]}) is None
    assert spec.clean({'schemas': spec.protect([None, None])}) == {'schemas': []}
    assert spec.clean({'schemas': [None, spec.protect(None)]}) == {'schemas': [None]}
    assert spec.clean({'schemas': spec.protect({'a': None})}) == {'schemas': {}}
    assert spec.clean({'schema': {'required': False}}) == {'schema': {'required': False}}
    assert spec.clean({'schemas': spec.skip([None, None])}) == {'schemas': [None, None]}


def test_merger():
    assert spec.merge({'a': [1, 2], 'b': {'c': 1}}, {'a': [3]}) == {'a': [1, 2, 3], 'b': {'c': 1}}
    assert spec.merge({'a': {'b': [1]}}, {'a': {'b': [2]}}) == {'a': {'b': [1, 2]}}
    assert spec.merge({'a': {'b': 1}}, {'a': {'b': 2}}) == {'a': {'b': 2}}
