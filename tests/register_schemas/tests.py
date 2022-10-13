from . import openapi
from tests.utils import itemgetter


def test_oas(get_oas):
    spec = get_oas(openapi)
    schemas = list(itemgetter(spec, 'components.schemas').values())
    assert len(schemas) == 2
    assert 'required' in schemas[0]
