def _is_immutable(self):
    raise TypeError(f"{type(self).__name__!r} objects are immutable")


class ImmutableDict(dict):
    def setdefault(self, key, default=None):
        _is_immutable(self)

    def update(self, *args, **kwargs):
        _is_immutable(self)

    def pop(self, key, default=None):
        _is_immutable(self)

    def popitem(self):
        _is_immutable(self)

    def __setitem__(self, key, value):
        _is_immutable(self)

    def __delitem__(self, key):
        _is_immutable(self)

    def clear(self):
        _is_immutable(self)
