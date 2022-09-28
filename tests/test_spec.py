from django_openapi.spec import utils as _spec
from django_openapi.schema import schemas


def test_spec_clean():
    assert _spec.clean({'schemas': ['name1', None]}) == {'schemas': ['name1']}
    assert _spec.clean({'schemas': [None, None]}) is None
    assert _spec.clean({'schemas': _spec.Protect([None, None])}) == {'schemas': []}
    assert _spec.clean({'schemas': [None, _spec.Protect(None)]}) == {'schemas': [None]}
    assert _spec.clean({'schemas': _spec.Protect({'a': None})}) == {'schemas': {}}
    assert _spec.clean({'schema': {'required': False}}) == {'schema': {'required': False}}
    assert _spec.clean({'schemas': _spec.Skip([None, None])}) == {'schemas': [None, None]}


def test_merger():
    assert _spec.merge({'a': [1, 2], 'b': {'c': 1}}, {'a': [3]}) == {'a': [1, 2, 3], 'b': {'c': 1}}
    assert _spec.merge({'a': {'b': [1]}}, {'a': {'b': [2]}}) == {'a': {'b': [1, 2]}}
    assert _spec.merge({'a': {'b': 1}}, {'a': {'b': 2}}) == {'a': {'b': 2}}


def test_schema_any():
    assert _spec.clean(schemas.Any(nullable=False).to_spec()) == {}
