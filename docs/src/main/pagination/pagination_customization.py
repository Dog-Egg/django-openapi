from django.db import models

from django_openapi import Resource, model2schema, schema
from django_openapi.pagination import Pagination
from django_openapi.parameter import Query


class MyPagination(Pagination):
    """自定义的分页器"""

    def __init__(self, schema):
        self.schema = schema

    def _get_request_parameter(self):
        return Query(
            {
                "page": schema.Integer(
                    default=1,
                    minimum=1,
                    alias="p",
                    description="页码",
                )
            }
        )

    def _get_response_schema(self):
        return schema.Model.from_dict(
            {
                "items": schema.List(self.schema),
                "total": schema.Integer(),
            }
        )()

    def _get_response(self, queryset, reqarg):
        page_size = 20
        offset = (reqarg["page"] - 1) * page_size
        return {
            "items": queryset[offset : offset + page_size],
            "total": queryset.count(),
        }


class Book(models.Model):
    title = models.CharField(max_length=20)
    author = models.CharField(max_length=20)


@Resource("/books")
class BooksAPI:
    def get(
        self,
        pagination=MyPagination(model2schema(Book)),
    ):
        return pagination.paginate(Book.objects.all())
