from django_openapi.parameters import Body, Query
from django_openapi.schema import schemas
from django_openapi.spec import Example
from tests.utils import itemgetter, TestResource


def test_oas_servers(oas):
    assert itemgetter(oas, 'servers') == [{'description': '测试服务器', 'url': 'https://example.com/spec'}]


def test_oas_schema_description(oas):
    assert itemgetter(oas, ['components', 'schemas', 'b4e958c9.Schema1', 'description']) == 'doc 1'
    assert itemgetter(oas, 'paths./foo.get.responses.200.content.application/json.schema.properties') == {
        "s11": {
            "$ref": "#/components/schemas/b4e958c9.Schema1"
        },
        "s12": {
            "$ref": "#/components/schemas/b4e958c9.Schema1"
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


@TestResource('/example')
class ExampleAPI:
    def post(self, body=Body(schemas.Model.from_dict({'a': schemas.Integer()})(example={}))):
        pass


def test_example(oas):
    assert itemgetter(oas, ['paths', '/example', 'post', 'requestBody', 'content', 'application/json', 'schema',
                            'example']) == {}


# test examples
@TestResource('/examples')
class ExamplesAPI:
    def post(self,
             body=Body(examples=[
                 Example(1),
                 Example({}, summary='空对象'),
                 Example({'a': []}, description='description 1')
             ]),
             query=Query({'a': schemas.Any(
                 examples=[
                     Example(1),
                     Example('a', description='description 2')
                 ])})
             ):
        pass


def test_examples(oas):
    assert itemgetter(oas, 'paths./examples.post.requestBody.content.application/json.examples') == {
        'Example 1': {'value': 1},
        'Example 2': {'summary': '空对象', 'value': {}},
        'Example 3': {'description': 'description 1', 'value': {'a': []}}
    }

    assert itemgetter(oas, ['paths', '/examples', 'post', 'parameters', 0, 'examples']) == {
        'Example 1': {'value': 1},
        'Example 2': {
            'description': 'description 2',
            'value': 'a',
        }
    }
