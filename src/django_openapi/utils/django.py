import functools

from django.core.exceptions import ValidationError as DjangoValidationError

from django_openapi import schema


def django_validator_wraps(fn):
    """把 Django 的验证器包装成 Schema 验证器，验证失败将抛出 `ValidationError <django_openapi.schema.ValidationError>` 异常对象。

    .. doctest::

        >>> from django.core.validators import validate_email
        >>> from django_openapi.utils.django import django_validator_wraps

        >>> validate = django_validator_wraps(validate_email)

        >>> validate('123@example.com') # That's right

        >>> validate('example@@')
        Traceback (most recent call last):
            ...
        django_openapi_schema.exceptions.ValidationError: [{'msgs': ['Enter a valid email address.']}]
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except DjangoValidationError as exc:
            raise schema.ValidationError(list(exc)[0]) from exc

    return wrapper
