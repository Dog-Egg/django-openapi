import re
from decimal import Decimal

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


class RegExp(Validator):
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def validate(self, value) -> None:
        if not self.pattern.search(value):
            raise DeserializationError('%s does not match pattern %s' % (value, self.pattern.pattern))


class Range(Validator):
    def __init__(self, *, gt=None, gte=None, lt=None, lte=None):
        # check
        self.__check_either_or(gt=gt, gte=gte)
        self.__check_either_or(lt=lt, lte=lte)

        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte

    @staticmethod
    def __check_either_or(**kwargs):
        assert len(kwargs) == 2
        if all(map(lambda x: x is not None, kwargs.values())):
            raise ValueError('Can only use one of %r or %r.' % tuple(kwargs))

    def validate(self, value):
        if self.gt is not None and self.lt is not None:
            if not (self.gt < value < self.lt):
                raise DeserializationError('The value must be greater than %s and less than %s' % (self.gt, self.lt))
        elif self.gt is not None and self.lte is not None:
            if not (self.gt < value <= self.lte):
                raise DeserializationError(
                    'The value must be greater than %s and less than or equal to %s' % (self.gt, self.lte))
        elif self.gte is None and self.lte is not None:
            if not (self.gte <= value <= self.lte):
                raise DeserializationError(
                    'The value must be greater than or equal to %s and less than or equal to %s' % (self.gte, self.lte))
        elif self.gte is not None and self.lt is not None:
            if not (self.gte <= value < self.lt):
                raise DeserializationError(
                    'The value must be greater than or equal to %s and less than %s' % (self.gte, self.lte))
        elif self.gt is not None:
            if not (self.gt < value):
                raise DeserializationError('The value must be greater than %s' % self.gt)
        elif self.gte is not None:
            if not (self.gte <= value):
                raise DeserializationError('The value must be greater than or equal to %s' % self.gte)
        elif self.lt is not None:
            if not (value < self.lt):
                raise DeserializationError('The value must be less than %s' % self.lt)
        elif self.lte is not None:
            if not (value <= self.lte):
                raise DeserializationError('The value must be less than or equal to %s' % self.lte)


class MultipleOf(Validator):
    def __init__(self, multiple):
        if multiple <= 0:
            raise ValueError('The value of "multipleOf" must be a number, strictly greater than 0')

        # Decimal 处理浮点数运算
        self.multiple = Decimal(str(multiple))

    def validate(self, value) -> None:
        if Decimal(str(value)) % self.multiple != 0:
            raise DeserializationError('The value must be a multiple of %s' % self.multiple)


class Choices(Validator):
    def __init__(self, choices):
        self.choices = set(choices or [])

    def validate(self, value) -> None:
        if value not in self.choices:
            raise DeserializationError('必须是 %s 中的一个' % list(self.choices))
