from . import openapi
from tests.utils import itemgetter


def find(schemas, fn):
    for s in schemas:
        if fn(s):
            yield s[1]


def test_oas(get_oas):
    spec = get_oas(openapi)
    schemas = list(itemgetter(spec, 'components.schemas').items())

    assert len(schemas) == 3

    # 手动注册的Schema
    for x in find(schemas, lambda o: '.' not in o[0]):
        assert 'required' in x

    # 自动注册的Schema
    for x in find(schemas, lambda o: o[0].endswith('.SchemaA')):
        assert 'required' not in x
