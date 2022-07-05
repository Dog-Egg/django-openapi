import abc


class RouterABC(abc.ABC):
    @abc.abstractmethod
    def add_route(self, route, apicls):
        pass


class Router(RouterABC):
    def __init__(self, *, prefix: str = None):
        self._prefix = prefix or '/'
        self._children = {}

    def add_route(self, route, apicls):
        full_route = self._join(self._prefix, route)
        child = self.__class__(prefix=full_route)
        if full_route in self._children:
            raise ValueError('Route %r already exists' % full_route)
        self._children[full_route] = (child, apicls)
        return child

    @staticmethod
    def _join(prefix: str, route: str):
        paths = []
        for part in [prefix, route]:
            for x in part.split('/'):
                if x:
                    paths.append(x)

        endpoint = '/' if route.endswith('/') else ''
        return '/'.join(paths) + endpoint

    def get_routes(self):
        routes = []

        def inner(children):
            for route, (child, apicls) in children.items():
                child: Router
                routes.append((route, apicls))
                inner(child._children)

        inner(self._children)
        return routes
