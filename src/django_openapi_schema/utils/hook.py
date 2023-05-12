import copy
import inspect
import typing as t
import uuid
from collections import defaultdict


class HookWrapper:
    def __init__(
        self,
        fn,
        key,
        payload: t.Any = None,
        unique_within_a_single_class=False,  # 检查该类型 hook 是否在单个类域内唯一。
    ):
        self.fn = fn
        self._method_name = None
        self._key = key
        self._bound = None
        self.payload = payload
        self.unique_within_a_single_class = unique_within_a_single_class

    @property
    def key(self):
        if inspect.isfunction(self._key):
            return self._key()
        return self._key

    def set_method_name(self, name: str):
        self._method_name = name

    def __call__(self, *args, **kwargs):
        self._method_name = t.cast(str, self._method_name)
        return getattr(self._bound, self._method_name)(*args, **kwargs)

    def bind(self, o):
        new = copy.copy(self)
        new._bound = o
        return new


class HookFunction:
    __hooks__: t.List[HookWrapper]


class HookClassMeta(type):
    __schema_hooks__: t.Mapping[t.Hashable, t.List[HookWrapper]]

    def __new__(mcs, classname, bases, attrs: dict):
        hooks_dict: t.Dict[str, t.List[HookWrapper]] = defaultdict(list)

        for name, value in attrs.copy().items():
            if isinstance(value, (classmethod, staticmethod)):
                fn = value.__func__
            elif inspect.isfunction(value):
                fn = value
            else:
                continue

            if not hasattr(fn, "__hooks__"):
                continue

            method_name = fn.__name__ + ":" + uuid.uuid4().hex
            fn = t.cast(HookFunction, fn)
            for hook in fn.__hooks__:
                hook.set_method_name(method_name)
                hooks_dict[hook.key].append(hook)

            attrs[method_name] = attrs[name]
            del attrs[name]

        # check
        for key, hooks in hooks_dict.items():
            if hooks[0].unique_within_a_single_class and len(hooks) > 1:
                raise RuntimeError(
                    "The hook <%r> can only define one in class %s, but find %s."
                    % (key, classname, list(map(lambda h: h.fn.__name__, hooks)))
                )

        attrs["__schema_hooks__"] = hooks_dict
        return super().__new__(mcs, classname, bases, attrs)


def set_hook(fn: t.Callable[..., t.Any], *args, **kwargs):
    hook = HookWrapper(fn, *args, **kwargs)
    try:
        hooks = getattr(fn, "__hooks__")
    except AttributeError:
        hooks = []
        setattr(fn, "__hooks__", hooks)
    hooks.append(hook)
    return fn


def get_hook(bound, key) -> t.Optional[HookWrapper]:
    for hook in iter_hooks(bound, key):
        return hook
    return None


def iter_hooks(bound, key) -> t.Generator[HookWrapper, None, None]:
    cls = bound if inspect.isclass(bound) else type(bound)
    for c in inspect.getmro(cls):
        if isinstance(c, HookClassMeta):
            c = t.cast(HookClassMeta, c)
            for hook in c.__schema_hooks__[key]:
                yield hook.bind(bound)
