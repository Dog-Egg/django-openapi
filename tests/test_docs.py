"""测试文档目录内 *.py 的示例代码；
加载模块，获取提取路由并设置到 django 路由表中。
"""

import functools
from importlib import import_module

import pytest
from django.test import override_settings
from django.urls import include, path


def load_openapi_module(module_name):
    module = import_module(module_name)

    def get_urlconf(module):
        from devtools import get_openapi_from_module

        # 从模块中解析出 urlpatterns
        openapi = get_openapi_from_module(module)
        urlpatterns = [
            path("", include(openapi.urls)),
        ]
        setattr(module, "urlpatterns", urlpatterns)

        return module

    def decorator(fn):
        @override_settings(ROOT_URLCONF=get_urlconf(module))
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            return fn(*args, **kwargs)

        return wrapper

    return decorator


@load_openapi_module("docs.src.main.pagination.pagination_customization")
@pytest.mark.django_db
def test_pagination_customization(client):
    from docs.src.main.pagination import pagination_customization as module

    module.Book.objects.bulk_create([module.Book(title="三体", author="老刘")] * 30)

    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == {
        "items": [{"author": "老刘", "id": i, "title": "三体"} for i in range(1, 21)],
        "total": 30,
    }


@load_openapi_module("docs.src.examples.restful")
@pytest.mark.django_db
def test_restful(client):
    from docs.src.examples import restful as module

    # 增
    response = client.post(
        "/books", data={"title": "三体", "author": "刘慈欣"}, content_type="application/json"
    )
    assert response.status_code == 201
    assert response.json() == {"author": "刘慈欣", "id": 1, "title": "三体"}

    # 分页查
    response = client.get("/books")
    assert response.status_code == 200
    assert response.json() == {
        "count": 1,
        "page": 1,
        "page_size": 20,
        "results": [{"author": "刘慈欣", "id": 1, "title": "三体"}],
    }

    # id 查
    response = client.get("/books/1")
    assert response.status_code == 200
    assert response.json() == {"author": "刘慈欣", "id": 1, "title": "三体"}

    # 404
    response = client.get("/books/999")
    assert response.status_code == 404

    # 改
    response = client.put("/books/1", {"author": "老刘"}, content_type="application/json")
    assert response.status_code == 400
    assert response.json() == {
        "errors": {"fields": [{"loc": ["title"], "msgs": ["This field is required."]}]}
    }

    response = client.put(
        "/books/1", {"title": "三体", "author": "老刘"}, content_type="application/json"
    )
    assert response.json() == {"author": "老刘", "id": 1, "title": "三体"}

    response = client.patch(
        "/books/1", {"title": "小说"}, content_type="application/json"
    )
    assert response.json() == {"author": "老刘", "id": 1, "title": "小说"}

    # 删
    response = client.delete("/books/1")
    assert response.status_code == 204
    assert module.Book.objects.filter(id=1).first() is None


@load_openapi_module("docs.src.main.permission.example")
def test_permission(client, django_user_model, admin_client):
    resp = client.get("/to/path")
    assert resp.status_code == 401

    user = django_user_model.objects.create(
        username="someone", password="something"
    )  # 普通用户
    client.force_login(user)
    resp = client.get("/to/path")
    assert resp.status_code == 403

    resp = admin_client.get("/to/path")
    assert resp.status_code == 200
