import re
from decimal import Decimal

from django_openapi.schema.exceptions import ValidationError


class LengthValidator:
    def __init__(self, min_length: int = None, max_length: int = None):
        self.min_length = min_length
        self.max_length = max_length

    def __call__(self, value):
        length = len(value)
        if self.min_length is not None and self.max_length is not None:
            if not (self.min_length <= length <= self.max_length):
                raise ValidationError('长度必须在 %d 到 %d 之间' % (self.min_length, self.max_length))
        elif self.min_length is not None:
            if length < self.min_length:
                raise ValidationError('长度最小为 %s' % self.min_length)
        elif self.max_length is not None:
            if length > self.max_length:
                raise ValidationError('长度最大为 %s' % self.max_length)


class RegExpValidator:
    def __init__(self, pattern):
        self.pattern = re.compile(pattern)

    def __call__(self, value) -> None:
        if not self.pattern.search(value):
            raise ValidationError('%s does not match pattern %s' % (value, self.pattern.pattern))


class RangeValidator:
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

    def __call__(self, value):
        if self.gt is not None and self.lt is not None:
            if not (self.gt < value < self.lt):
                raise ValidationError('The value must be greater than %s and less than %s' % (self.gt, self.lt))
        elif self.gt is not None and self.lte is not None:
            if not (self.gt < value <= self.lte):
                raise ValidationError(
                    'The value must be greater than %s and less than or equal to %s' % (self.gt, self.lte))
        elif self.gte is None and self.lte is not None:
            if not (self.gte <= value <= self.lte):
                raise ValidationError(
                    'The value must be greater than or equal to %s and less than or equal to %s' % (self.gte, self.lte))
        elif self.gte is not None and self.lt is not None:
            if not (self.gte <= value < self.lt):
                raise ValidationError(
                    'The value must be greater than or equal to %s and less than %s' % (self.gte, self.lte))
        elif self.gt is not None:
            if not (self.gt < value):
                raise ValidationError('The value must be greater than %s' % self.gt)
        elif self.gte is not None:
            if not (self.gte <= value):
                raise ValidationError('The value must be greater than or equal to %s' % self.gte)
        elif self.lt is not None:
            if not (value < self.lt):
                raise ValidationError('The value must be less than %s' % self.lt)
        elif self.lte is not None:
            if not (value <= self.lte):
                raise ValidationError('The value must be less than or equal to %s' % self.lte)


class MultipleOfValidator:
    def __init__(self, multiple):
        if multiple <= 0:
            raise ValueError('The value of "multipleOf" must be a number, strictly greater than 0')

        # Decimal 处理浮点数运算
        self.multiple = Decimal(str(multiple))

    def __call__(self, value) -> None:
        if Decimal(str(value)) % self.multiple != 0:
            raise ValidationError('The value must be a multiple of %s' % self.multiple)


class ChoicesValidator:
    def __init__(self, choices):
        self.choices = set(choices or [])

    def __call__(self, value) -> None:
        if value not in self.choices:
            raise ValidationError('必须是 %s 中的一个' % list(self.choices))


def unique_validate(items):
    tmp = []
    for item in items:
        if item in tmp:
            raise ValidationError('The item is not unique')
        tmp.append(item)
