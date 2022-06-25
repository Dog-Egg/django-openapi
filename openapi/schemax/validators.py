from openapi.schemax.exceptions import ValidationError


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
                raise ValidationError('长度必须在 %d 到 %d 之间' % (self.min, self.max))
        elif self.min is not None:
            if length < self.min:
                raise ValidationError('长度最小为 %s' % self.min)
        elif self.max is not None:
            if length > self.max:
                raise ValidationError('长度最大为 %s' % self.max)
