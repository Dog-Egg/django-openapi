import importlib
import inspect
import operator
import typing

T = typing.TypeVar("T")


def make_instance(obj: typing.Union[T, typing.Type[T]]) -> T:
    if isinstance(obj, type):
        return obj()
    return obj


def import_string(obj_path: str, default_module: str = ""):
    """
    >>> import math
    >>> import_string('math.pi') == math.pi
    True
    """
    if ":" in obj_path:
        module, obj = obj_path.rsplit(":", 1)
    elif "." in obj_path:
        module, obj = obj_path.rsplit(".", 1)
    else:
        module, obj = default_module, obj_path

    return operator.attrgetter(obj)(importlib.import_module(module))
