from django.db import models

from django_openapi import Operation, Resource, model2schema
from django_openapi.parameter import Body


class OneModel(models.Model):
    BigIntegerField = models.BigIntegerField()
    BooleanField = models.BooleanField()
    CharField = models.CharField()
    DateField = models.DateField()
    DateTimeField = models.DateTimeField()
    FileField = models.FileField()
    DecimalField = models.DecimalField()


@Resource("/to/path")
class API:
    @Operation(response_schema=model2schema(OneModel))
    def get(self):
        ...
