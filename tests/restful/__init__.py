from tests.utils import TestOpenAPI
from . import views

openapi = TestOpenAPI(title='Restful API')
openapi.find_resources(views)
