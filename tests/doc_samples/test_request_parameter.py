import pytest
from django.http import QueryDict, HttpRequest

from openapi import API, Operation
from openapi.parameters import Query
from openapi.schema import schemas


def test_sample1():
    from openapi import API
    from openapi.parameters import Query
    from openapi.schema import schemas

    class SearchSchema(schemas.Model):
        # 定义 search 的参数结构
        name = schemas.String(description='名称', required=False)
        status = schemas.Integer(description='状态', required=False)

    class MyAPI(API):
        # highlight-next-line
        def get(self, request, search=Query(SearchSchema)):
            # do something...
            pass

    # #
    assert SearchSchema().deserialize(QueryDict('name=foo&status=1&xx=...')) == {'name': 'foo', 'status': 1}
    assert SearchSchema().deserialize(QueryDict('name=&status=')) == {}


def test_sample2():
    class MyAPI(API):
        # highlight-next-line
        def get(self, request, search=Query({
            'name': schemas.String(description='名称', required=False),
            'status': schemas.Integer(description='状态', required=False)
        })):
            # ...
            pass

    # #
    with pytest.raises(ValueError, match='Need a schema.Model object'):
        Query(schemas.List())


def test_sample3():
    operation = Operation()

    class SearchSchema(schemas.Model):
        # 定义 search 的参数结构
        name = schemas.String(description='名称', required=False)
        status = schemas.Integer(description='状态', required=False)

    class PaginationSchema(schemas.Model):
        page = schemas.Integer(default=1, gte=1)
        page_size = schemas.Integer(default=100, gte=10, lte=500)

    class MyAPI(API):
        @operation
        def get(self, request, search=Query(SearchSchema), pagination=Query(PaginationSchema)):
            # do something...
            pass

    req = HttpRequest()
    req.GET = QueryDict('name=foo&status=1&page=2')
    assert operation.parser.parse_request(req) == {'pagination': {'page': 2, 'page_size': 100},
                                                   'search': {'name': 'foo', 'status': 1}}
