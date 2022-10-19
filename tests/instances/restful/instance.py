from tests.utils import TestOpenAPI

openapi = TestOpenAPI(title='Restful API')
openapi.find_resources(__package__)
