"""https://validator.swagger.io"""
import json

import pytest
import requests
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse, NoReverseMatch
from django.test.client import RequestFactory

from tests.urls import instances


def get_spec_set():
    rf = RequestFactory()
    for _, openapi in instances:
        try:
            spec = openapi.get_spec(rf.get(reverse(openapi.spec_view)))
        except NoReverseMatch:
            spec = openapi.get_spec()
        yield json.loads(json.dumps(spec, cls=DjangoJSONEncoder))


@pytest.mark.parametrize('spec', get_spec_set())
def test_validate_spec(client, spec, request):
    if not request.config.getoption('--validate-oas'):
        pytest.skip('未开启验证')

    resp = requests.post('https://validator.swagger.io/validator/debug', json=spec)
    assert resp.status_code == 200
    assert resp.json() == {}  # 返回 {} 表示 spec 验证有效
