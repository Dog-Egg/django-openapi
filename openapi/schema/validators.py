from openapi.schema.exceptions import DeserializationError


class Validator:
    def validate(self, value) -> None:
        raise NotImplementedError


class Length(Validator):
    # noinspection PyShadowingBuiltins
    def __init__(self, min: int = None, max: int = None):
        self.min = min
        self.max = max

    def validate(self, value):
        length = len(value)
        if self.min is not None and self.max is not None:
            if not (self.min <= length <= self.max):
                raise DeserializationError('长度必须在 %d 到 %d 之间' % (self.min, self.max))
        elif self.min is not None:
            if length < self.min:
                raise DeserializationError('长度最小为 %s' % self.min)
        elif self.max is not None:
            if length > self.max:
                raise DeserializationError('长度最大为 %s' % self.max)


class Range(Validator):
    # noinspection PyShadowingBuiltins
    def __init__(self, min=None, max=None):
        self.min = min
        self.max = max

    def validate(self, value):
        if self.min is not None and self.max is not None:
            if not (self.min <= value <= self.max):
                raise DeserializationError('大小必须在 %d 到 %d 之间' % (self.min, self.max))
        elif self.min is not None:
            if value < self.min:
                raise DeserializationError('最小为 %s' % self.min)
        elif self.max is not None:
            if value > self.max:
                raise DeserializationError('最大为 %s' % self.max)


class Choices(Validator):
    def __init__(self, choices):
        self.choices = set(choices or [])

    def validate(self, value) -> None:
        if value not in self.choices:
            raise DeserializationError('必须是 %s 中的一个' % list(self.choices))
