import re


class _EnumMeta(type):
    def __new__(mcs, *args, **kwargs):
        return type.__new__(mcs, *args, **kwargs)

    def __init__(cls, name, bases, attrs):
        super().__init__(cls)
        cls.__mapping = {}
        cls.__values = set()

        # inherit
        for base in bases[::-1]:
            if isinstance(base, _EnumMeta):
                cls.__mapping.update(base.__mapping)
                cls.__values.update(base.__values)

        for name, value in attrs.items():
            if re.match('^__.*?__$', name):
                continue
            if value in cls.__values:
                raise ValueError('%r 已存在' % value)
            cls.__values.add(value)
            cls.__mapping[name] = value

    def __contains__(cls, item):
        return item in cls.__values

    def __iter__(self):
        return iter(self.__values)


class Enum(metaclass=_EnumMeta):
    def __new__(cls, *args, **kwargs):
        raise RuntimeError('枚举类不可实例化')
