import inspect


class PureObject:
    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)


def make_instance(obj):
    if inspect.isclass(obj):
        obj = obj()
    return obj
