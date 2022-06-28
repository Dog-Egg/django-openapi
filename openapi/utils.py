import inspect


def make_instance(obj):
    if inspect.isclass(obj):
        obj = obj()
    return obj
