import copy
import inspect

import typing
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.functional import cached_property

from django_openapi import model2schema
from django_openapi.parameters.parameters import BaseParameter, Query
from django_openapi.schema import schemas
from django_openapi.utils.functional import make_instance


class PageNumberPaginator(BaseParameter):
    __limit__ = 1

    page: schemas.Integer = schemas.Integer(gte=1, default=1)
    page_size: typing.Union[schemas.Integer, int] = schemas.Integer(gte=1, lte=1000, default=20)

    field_mapping: typing.Dict[str, str] = {}

    def __init__(self, schema):
        if inspect.isclass(schema) and issubclass(schema, models.Model):
            schema = model2schema(schema)
        self._inner_schema = make_instance(schema)
        self._query = Query(dict(
            page=self._response_schema.fields.page,
            page_size=isinstance(self.page_size, schemas.BaseSchema) and self._response_schema.fields.page_size,
        ))
        self.current_page = None
        self.current_page_size = None

    def setup(self, operation):
        if operation.response_schema is None:
            operation.response_schema = self._response_schema()

    @cached_property
    def _response_schema(self):
        return schemas.Model.from_dict(dict(
            count=schemas.Integer(alias=self.field_mapping.get('count')),
            page=self.page.copy_with(alias=self.field_mapping.get('page')),
            page_size=(self.page_size if isinstance(self.page_size, schemas.Integer) else schemas.Integer()).copy_with(
                alias=self.field_mapping.get('page_size')),
            results=schemas.List(self._inner_schema, alias=self.field_mapping.get('results'))
        ))

    def to_spec(self, spec_id):
        return self._query.to_spec(spec_id)

    def parse_request(self, request: HttpRequest):
        args = self._query.parse_request(request)

        this = copy.copy(self)
        this.current_page = args['page']
        this.current_page_size = args.get('page_size', self.page_size)

        return this

    def paginate(self, queryset: typing.Union[QuerySet, typing.Sequence]):
        offset = (self.current_page - 1) * self.current_page_size

        if isinstance(queryset, QuerySet):
            count = queryset.count()
        else:
            count = len(queryset)

        return dict(
            page=self.current_page,
            page_size=self.current_page_size,
            results=queryset[offset: offset + self.current_page_size],
            count=count,
        )
