from openapi.parameters import Query, Cookie, Body
from openapi.parameters.parse import ParameterParser
from openapi.schemax import fields


def test_parameter_parse():
    def handler(
            query=Query({
                'page': fields.Integer(default=1),
                'page_size': fields.Integer(default=100)
            }),
            cookies=Cookie({'api_key': fields.String(key='apiKey')}),
            body=Body({'username': fields.String(), 'password': fields.String()})
    ):
        pass

    parser = ParameterParser(handler)

    assert [p.serialize() for p in parser.get_spec_parameters()] == (
        [
            {'in': 'query', 'name': 'page', 'schema': {'type': 'integer', 'default': 1}},
            {'in': 'query', 'name': 'page_size', 'schema': {'type': 'integer', 'default': 100}},
            {'in': 'cookie', 'name': 'apiKey', 'required': True, 'schema': {'type': 'string'}}
        ])

    assert parser.get_spec_request_body().serialize() == (
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
