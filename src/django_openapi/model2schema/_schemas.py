import decimal

from django_openapi_schema import Schema


class Decimal(Schema):
    class Meta:
        data_type = "number"

    def _deserialize(self, value):
        return decimal.Decimal(str(value))

    def _serialize(self, value: decimal.Decimal):
        exponent = value.as_tuple().exponent
        if not isinstance(exponent, int):
            raise ValueError("Cannot serialize decimal: %s" % value)
        else:
            if exponent < 0:
                return float(value)
            return int(value)
