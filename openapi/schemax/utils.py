from collections.abc import Iterable


class PureObject(Iterable):
    def __init__(self, **attributes):
        self.__attributes = attributes
        for name, value in attributes.items():
            setattr(self, name, value)

    def __iter__(self):
        return iter(self.__attributes.items())
