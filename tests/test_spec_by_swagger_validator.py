"""https://validator.swagger.io"""
import json
import os

import pytest
import requests
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse, NoReverseMatch
from django.test.client import RequestFactory

from django_openapi import OpenAPI


def get_spec_set():
    rf = RequestFactory()
    for openapi in OpenAPI._instances:
        try:
            spec = openapi.get_spec(rf.get(reverse(openapi.spec_view)))
        except NoReverseMatch:
            spec = openapi.get_spec()
        yield json.loads(json.dumps(spec, cls=DjangoJSONEncoder))


@pytest.mark.order("last")
@pytest.mark.parametrize('spec', get_spec_set())
@pytest.mark.skipif('TOX_ENV_NAME' not in os.environ, reason='比较慢，在 tox 中执行吧')
def test_validate_spec(client, spec):
    resp = requests.post('https://validator.swagger.io/validator/debug', json=spec)
    assert resp.status_code == 200
    assert resp.json() == {}  # 返回 {} 表示 spec 验证有效
