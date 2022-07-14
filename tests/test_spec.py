from openapi import spec


def test_spec_clean():
    assert spec.clean({'schemas': ['name1', None]}) == {'schemas': ['name1']}
    assert spec.clean({'schemas': [None, None]}) is None
    assert spec.clean({'schemas': spec.protect([None, None])}) == {'schemas': []}
    assert spec.clean({'schemas': spec.protect({'a': None})}) == {'schemas': {}}
