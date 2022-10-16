from django.urls import path, include

import tests.restful
import tests.security
import tests.forbidden
import tests.response
import tests.specification
import tests.register_schemas
from django_openapi.docs import swagger_ui
from .utils import TestOpenAPI

openapi = TestOpenAPI(title='DjangoOpenAPI Tests')
openapi.find_resources(tests)

docs_view = swagger_ui(
    openapi,
    tests.restful.openapi,
    tests.security.openapi,
    tests.response.openapi,
    tests.specification.openapi,
    tests.forbidden.openapi,
    tests.register_schemas.openapi,
    load_local_static=True
)

urlpatterns = [
    path('', docs_view),
    path('', include(openapi.urls)),
    path('', include(tests.forbidden.openapi.urls)),
    path('response/', include(tests.response.openapi.urls)),
    path('schema/', include(tests.register_schemas.openapi.urls)),
    path('spec/', include(tests.specification.openapi.urls)),
    path('security/', include(tests.security.openapi.urls)),
    path('api/', include(tests.restful.openapi.urls)),
]
