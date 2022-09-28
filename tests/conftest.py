import pytest
from django.urls import reverse

from django_openapi import OpenAPI
from django_openapi.utils.functional import make_instance


@pytest.fixture
def to_spec():
    from django_openapi.spec import utils as _spec
    return lambda schema: _spec.clean(make_instance(schema).to_spec())


@pytest.fixture
def get_oas(client):
    def fn(openapi: OpenAPI = None):
        from .urls import openapi as default

        if openapi is None:
            openapi = default
        response = client.get(reverse(openapi.spec_view))
        return response.json()

    return fn
