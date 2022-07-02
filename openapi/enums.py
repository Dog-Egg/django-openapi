from openapi.utils.enum import Enum


class Location(Enum):
    QUERY = 'query'
    COOKIE = 'cookie'
    HEADER = 'header'
    PATH = 'path'


class JsonSchemaType(Enum):
    STRING = 'string'
    INTEGER = 'integer'
    OBJECT = 'object'
    ARRAY = 'array'


class SecurityType(Enum):
    API_KEY = 'apiKey'
    HTTP = 'http'
    OAUTH2 = 'oauth2'
    OPEN_ID_CONNECT = 'openIdConnect'
