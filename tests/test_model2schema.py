import os

import pytest

from openapi.extension.model2schema import model2schema
from openapi.schema import schemas


@pytest.mark.skip
def test_model2schema():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django.conf.global_settings')
    from django.db import models
    from django import setup
    setup()

    class DjangoModel(models.Model):
        a = models.CharField()
        b = models.CharField(max_length=30)

        class Meta:
            app_label = '__test__'

    schema_class = model2schema(DjangoModel)

    assert isinstance(schema_class.a, schemas.String)
    assert schema_class.b.max_length == 30
