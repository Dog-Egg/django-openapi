import abc


class RouterABC(abc.ABC):
    @abc.abstractmethod
    def add_route(self, route, apicls):
        pass


class Router(RouterABC):
    def __init__(self, *, prefix: str = None):
        self._prefix = prefix or '/'
        self._children = {}

    def add_route(self, path, apicls):
        full_path = join_path(self._prefix, path)
        child = self.__class__(prefix=full_path)
        if full_path in self._children:
            raise ValueError('Route %r already exists' % full_path)
        self._children[full_path] = (child, apicls)
        return child

    def get_routes(self):
        routes = []

        def inner(children):
            for path, (child, apicls) in children.items():
                child: Router
                routes.append((path, apicls))
                inner(child._children)

        inner(self._children)
        return routes


def join_path(prefix, path):
    paths = []
    for part in [prefix, path]:
        for x in part.split('/'):
            if x:
                paths.append(x)

    endpoint = '/' if path.endswith('/') else ''
    return '/'.join(paths) + endpoint
