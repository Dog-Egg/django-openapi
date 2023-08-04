import datetime

import pytest

from django_openapi import schema


def test_Datetime__USE_TZ__True(settings):
    settings.USE_TZ = True

    with pytest.raises(schema.ValidationError):
        try:
            schema.Datetime().deserialize("2022-01-01")
        except schema.ValidationError as e:
            assert e.format_errors() == [
                {"msgs": ["Not support timezone-naive datetime."]}
            ]
            raise

    assert schema.Datetime().deserialize("2022-01-01T08:12+07") == datetime.datetime(
        2022, 1, 1, 8, 12, tzinfo=datetime.timezone(datetime.timedelta(hours=7))
    )


def test_Datetime__USE_TZ__False(settings):
    settings.USE_TZ = False

    with pytest.raises(schema.ValidationError):
        try:
            schema.Datetime().deserialize("2022-01-01T08:12+07")
        except schema.ValidationError as e:
            assert e.format_errors() == [
                {"msgs": ["Not support timezone-aware datetime."]}
            ]
            raise

    assert schema.Datetime().deserialize("2022-01-01") == datetime.datetime(2022, 1, 1)
