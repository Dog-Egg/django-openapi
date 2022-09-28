from tests.specification import openapi
from tests.utils import itemgetter


def test_oas_servers(get_oas):
    oas = get_oas(openapi)
    assert itemgetter(oas, 'servers') == [{'description': '测试服务器', 'url': 'https://example.com/spec'}]


def test_oas_schema_description(get_oas):
    oas = get_oas(openapi)
    assert itemgetter(oas, ['components', 'schemas', '293d6545.Schema1', 'description']) == 'doc 1'
    assert itemgetter(oas, 'paths./foo.get.responses.200.content.application/json.schema.properties') == {
        "s11": {
            "$ref": "#/components/schemas/293d6545.Schema1"
        },
        "s12": {
            "$ref": "#/components/schemas/293d6545.Schema1"
        },
        "s21": {
            "type": "object",
            "description": "desc 2"
        },
        "s22": {
            "type": "object",
            "description": "doc 2"
        }
    }
