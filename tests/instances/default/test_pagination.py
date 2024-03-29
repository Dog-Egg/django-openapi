"""分页器"""
from django_openapi import Operation
from django_openapi.schema import schemas
from django_openapi.pagination import PageNumberPaginator
from django_openapi.urls import reverse
from tests.utils import TestResource, ResourceView, itemgetter

ALL_BOOKS = [dict(id=i, title='书名') for i in range(1, 150)]


class BookSchema(schemas.Model):
    id = schemas.Integer(description='ID')
    title = schemas.String(description='书名')


@TestResource
class ResourceA(ResourceView):
    @staticmethod
    def get(paginator=PageNumberPaginator(BookSchema)):
        return paginator.paginate(ALL_BOOKS)

    class PageNumberPaginator2(PageNumberPaginator):
        page_size = 30

    @Operation(summary='固定 page_size')
    def post(self, paginator=PageNumberPaginator2(BookSchema)):
        return paginator.paginate(ALL_BOOKS)

    class PageNumberPaginator3(PageNumberPaginator):
        field_mapping = {
            'page': 'p',
            'page_size': 'pageSize',
            'count': 'total',
            'results': 'books'
        }

    @staticmethod
    @Operation(summary='字段名称映射')
    def put(paginator=PageNumberPaginator3(BookSchema)):
        return paginator.paginate(ALL_BOOKS)


def test_pagination(client, oas):
    resp = client.get(reverse(ResourceA))
    data = resp.json()
    assert len(data['results']) == 20
    assert data['page'] == 1
    assert data['page_size'] == 20
    assert data['count'] == 149

    assert itemgetter(oas, oas_response_properties_path('get'))['page_size'] == {
        'type': 'integer',
        'default': 20,
        'maximum': 1000,
        'minimum': 1
    }


def test_fixed_page_size(client, oas):
    """固定 page_size"""
    resp = client.post(f'{reverse(ResourceA)}?page=5')
    data = resp.json()
    assert len(data['results']) == 29
    assert data['page_size'] == 30

    # 固定 page_size
    assert itemgetter(oas, oas_response_properties_path('post'))['page_size'] == {
        'type': 'integer'
    }
    parameters = itemgetter(oas, f'paths.{reverse(ResourceA)}.post.parameters')
    assert len(parameters) == 1
    assert parameters[0]['name'] == 'page'  # 固定 page_size 后，请求参数只有page


def test_field_mapping(oas):
    parameters = itemgetter(oas, f'paths.{reverse(ResourceA)}.put.parameters')
    assert parameters[0]['name'] == 'p'
    assert parameters[1]['name'] == 'pageSize'

    resp_props = itemgetter(oas, oas_response_properties_path('put'))
    assert resp_props.__len__() == 4
    assert set(resp_props.keys()) == {'p', 'pageSize', 'total', 'books'}


def oas_response_properties_path(method):
    return [
        'paths', reverse(ResourceA), method, 'responses', '200', 'content', 'application/json',
        'schema', 'properties'
    ]
