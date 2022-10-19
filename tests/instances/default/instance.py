from tests.utils import TestOpenAPI

openapi = TestOpenAPI(title='DjangoOpenAPI Tests')
openapi.find_resources(__package__)

__prefix__ = ''
