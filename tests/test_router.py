import pytest

from openapi.router import Router


def test_router():
    router = Router(prefix='/api')

    router.add_route('users', None) \
        .add_route('/{user_id}', None) \
        .add_route('friends/', None) \
        .add_route('{friend_id}', None)

    router.add_route('books', None) \
        .add_route('{book_id}', None)

    assert [
               ('api/users', None),
               ('api/users/{user_id}', None),
               ('api/users/{user_id}/friends/', None),
               ('api/users/{user_id}/friends/{friend_id}', None),
               ('api/books', None),
               ('api/books/{book_id}', None)
           ] == router.get_routes()


def test_router_error():
    router = Router()
    router.add_route('user', None)
    with pytest.raises(ValueError):
        router.add_route('/user', None)

    router.add_route('user/', None)
    router.add_route('user/123', None)


def test_router_demo():
    router1 = Router()
    router1.add_route('books', None)
    router1.add_route('books/123', None)

    router2 = Router()
    router2.add_route('books', None).add_route('123', None)

    assert router1.get_routes() == router2.get_routes()
