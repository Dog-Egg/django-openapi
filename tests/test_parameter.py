from openapi import spec
from openapi.parameters import Query, Cookie, Body
from openapi.parameters.parse import ParameterParser
from openapi.schema import schemas


def test_parameter_parse():
    def handler(
            query=Query({
                'page': schemas.Integer(default=1),
                'page_size': schemas.Integer(default=100)
            }),
            cookies=Cookie({'api_key': schemas.String(alias='apiKey')}),
            body=Body({'username': schemas.String(), 'password': schemas.String()})
    ):
        pass

    parser = ParameterParser(handler)

    assert spec.clean(parser.get_spec_parameters()) == (
        [
            {'in': 'query', 'name': 'page', 'schema': {'type': 'integer', 'default': 1}},
            {'in': 'query', 'name': 'page_size', 'schema': {'type': 'integer', 'default': 100}},
            {'in': 'cookie', 'name': 'apiKey', 'required': True, 'schema': {'type': 'string'}}
        ])

    assert spec.clean(parser.get_spec_request_body()) == (
        {
            'content': {
                'application/json': {
                    'schema': {
                        'properties': {
                            'password': {'type': 'string'},
                            'username': {'type': 'string'}
                        },
                        'required': [
                            'username',
                            'password'
                        ],
                        'type': 'object'
                    }
                }
            },
            'required': True
        })
