from django.db import models

from django_openapi import Resource, model2schema
from django_openapi.pagination import OffsetPagination, PagePagination


class User(models.Model):
    username = models.CharField()
    address = models.CharField()


@Resource("/users")
class UsersAPI:
    def get(
        self,
        pagination=PagePagination(model2schema(User)),
    ):
        return pagination.paginate(User.objects.all())

    def post(
        self,
        pagination=OffsetPagination(model2schema(User)),
    ):
        return pagination.paginate(User.objects.all())
