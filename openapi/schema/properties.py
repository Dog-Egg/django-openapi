import typing


class Property:
    def __init__(self):
        pass

    def deserialize(self, value):
        raise NotImplementedError

    # def serialize(self, value):
    #     raise NotImplementedError


class Schema(Property):
    _properties: typing.Dict[str, Property]

    def __init_subclass__(cls, **kwargs):
        cls._properties = {}
        for name, value in vars(cls).items():
            if isinstance(value, Property):
                cls._properties[name] = value

    def deserialize(self, value):
        kwargs = {}
        for name, prop in self._properties.items():
            kwargs[name] = prop.deserialize(value[name])

        instance = self.__class__()
        for k, v in kwargs.items():
            setattr(instance, k, v)
        return instance

    @classmethod
    def from_dict(cls, properties: typing.Dict[str, Property]):
        return type('GeneratedSchema', (cls,), properties.copy())


class String(Property):
    def deserialize(self, value):
        return str(value)


class Integer(Property):
    def deserialize(self, value):
        return int(value)
