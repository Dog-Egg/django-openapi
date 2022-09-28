from django.urls import reverse

from . import openapi


def test_apispec_permission(client):
    response = client.get(reverse(openapi.spec_view))
    assert response.status_code == 403
