import re
import typing as t
from decimal import Decimal

from .exceptions import ValidationError


class OneOf:
    def __init__(self, choices: t.Iterable):
        self._choices = choices

    def __call__(self, value):
        if value not in self._choices:
            raise ValidationError(
                f"The value must be one of {', '.join(repr(e) for e in self._choices)}."
            )


class RangeValidator:
    def __init__(self, *, gt=None, gte=None, lt=None, lte=None):
        if gt is not None and gte is not None:
            raise ValueError("Only one can be set for 'gt' and 'gte'.")
        if lt is not None and lte is not None:
            raise ValueError("Only one can be set for 'lt' and 'lte'.")

        self.gt = gt
        self.gte = gte
        self.lt = lt
        self.lte = lte

    def __call__(self, value):
        if self.gt is not None and self.lt is not None:
            if not (self.gt < value < self.lt):
                raise ValidationError(
                    "The value must be greater than %s and less than %s."
                    % (self.gt, self.lt)
                )
        elif self.gt is not None and self.lte is not None:
            if not (self.gt < value <= self.lte):
                raise ValidationError(
                    "The value must be greater than %s and less than or equal to %s."
                    % (self.gt, self.lte)
                )
        elif self.gte is None and self.lte is not None:
            if not (self.gte <= value <= self.lte):
                raise ValidationError(
                    "The value must be greater than or equal to %s and less than or equal to %s."
                    % (self.gte, self.lte)
                )
        elif self.gte is not None and self.lt is not None:
            if not (self.gte <= value < self.lt):
                raise ValidationError(
                    "The value must be greater than or equal to %s and less than %s."
                    % (self.gte, self.lte)
                )
        elif self.gt is not None:
            if not (self.gt < value):
                raise ValidationError("The value must be greater than %s." % self.gt)
        elif self.gte is not None:
            if not (self.gte <= value):
                raise ValidationError(
                    "The value must be greater than or equal to %s." % self.gte
                )
        elif self.lt is not None:
            if not (value < self.lt):
                raise ValidationError("The value must be less than %s." % self.lt)
        elif self.lte is not None:
            if not (value <= self.lte):
                raise ValidationError(
                    "The value must be less than or equal to %s." % self.lte
                )


class MultipleOfValidator:
    def __init__(self, multiple):
        if multiple <= 0:
            raise ValueError(
                'The value of "multipleOf" must be a number, strictly greater than 0'
            )

        # Decimal 处理浮点数运算
        self._multiple = Decimal(str(multiple))

    def __call__(self, value) -> None:
        if Decimal(str(value)) % self._multiple != 0:
            raise ValidationError(
                "The value must be a multiple of %s." % self._multiple
            )


class RegExpValidator:
    def __init__(self, pattern: t.Union[str, re.Pattern]):
        self.pattern = re.compile(pattern)

    def __call__(self, value) -> None:
        if not self.pattern.search(value):
            raise ValidationError(
                "%r does not match pattern %s." % (value, self.pattern.pattern)
            )


class LengthValidator:
    def __init__(
        self, min_length: t.Optional[int] = None, max_length: t.Optional[int] = None
    ):
        if min_length is None and max_length is None:
            raise ValueError("min_length or max_length cannot both be empty.")
        self.min_length = min_length
        self.max_length = max_length

    def __call__(self, value):
        length = len(value)
        if self.min_length is not None and self.max_length is not None:
            if not (self.min_length <= length <= self.max_length):
                raise ValidationError(
                    "The length must be between %d and %d."
                    % (self.min_length, self.max_length)
                )
        elif self.min_length is not None:
            if length < self.min_length:
                raise ValidationError(
                    "The length must be greater than or equal to %d." % self.min_length
                )
        elif self.max_length is not None:
            if length > self.max_length:
                raise ValidationError(
                    "The length must be less than or equal to %d." % self.max_length
                )


def unique_validate(items):
    unique = []
    for item in items:
        if item in unique:
            raise ValidationError("All of items must be unique.")
        unique.append(item)
