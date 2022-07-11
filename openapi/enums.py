from openapi.utils.enum import Enum


class Location(Enum):
    QUERY = 'query'
    COOKIE = 'cookie'
    HEADER = 'header'
    PATH = 'path'


class DataType(Enum):
    STRING = 'string'
    INTEGER = 'integer'
    NUMBER = 'number'
    BOOLEAN = 'boolean'
    OBJECT = 'object'
    ARRAY = 'array'


class DataFormat(Enum):
    DATETIME = 'date-time'
    DATE = 'date'
    FLOAT = 'float'
    DOUBLE = 'double'
    BINARY = 'binary'
    PASSWORD = 'password'


class SecurityType(Enum):
    API_KEY = 'apiKey'
    HTTP = 'http'
    OAUTH2 = 'oauth2'
    OPEN_ID_CONNECT = 'openIdConnect'
