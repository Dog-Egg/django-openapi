from collections import UserString


class Path(UserString):
    def __init__(self, route, **kwargs):
        super().__init__(route)
        self.path_parameters = kwargs
