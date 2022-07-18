import pytest
from django.db import models

from openapi.extension.model2schema import model_field_to_schema_field
from openapi.schema import schemas


@pytest.mark.skip
def test_model2schema():
    sf = model_field_to_schema_field(models.CharField(max_length=11))
    assert isinstance(sf, schemas.String)
    assert sf.max_length == 11
    assert sf.required is True

    sf = model_field_to_schema_field(models.IntegerField(default=1))
    assert isinstance(sf, schemas.Integer)
    assert sf.required is False
