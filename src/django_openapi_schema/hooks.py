import functools
import inspect
import types
import typing as t

from .schemas import Schema
from .utils.hook import set_hook

__all__ = (
    "serialization_fget",
    "validator",
)


def serialization_fget(field: t.Union[Schema, str]):
    """
    自定义 `Model` 序列化时字段取值。默认是对 `Mapping <collections.abc.Mapping>` 取索引，对其它对象取属性名。

    :param field: 字段或字段名，将取值函数应用于该字段。

    .. code-block::
        :emphasize-lines: 6

        >>> from django_openapi import schema

        >>> class Person(schema.Model):
        ...     fullname = schema.String()
        ...
        ...     @schema.serialization_fget(fullname)
        ...     def get_fullname(self, data):
        ...         return data['firstname'] + data['lastname']

        >>> Person().serialize({'firstname': '张', 'lastname': '三'})
        {'fullname': '张三'}
    """

    def decorator(method):
        return set_hook(
            method,
            lambda: (
                "serialization_fget",
                field._name if isinstance(field, Schema) else field,
            ),
            unique_within_a_single_class=True,
        )

    return decorator


def validator(__a=None):
    """
    定义校验函数。

    .. code-block::
        :emphasize-lines: 5

        >>> from django_openapi import schema

        >>> class PositiveInteger(schema.Integer):
        ...     \"""正整数\"""
        ...     @schema.validator
        ...     def validate(self, value):
        ...         if value <= 0:
        ...             raise schema.ValidationError('不是一个正整数')

        >>> PositiveInteger().deserialize(-1)
        Traceback (most recent call last):
            ...
        django_openapi_schema.exceptions.ValidationError: {'msgs': ['不是一个正整数']}

    如下是在 `Model` 中使用 `validator` 校验日期的正确性。

    .. code-block::
        :emphasize-lines: 5

        >>> class MySchema(schema.Model):
        ...     start_date = schema.Date()
        ...     end_date = schema.Date()
        ...
        ...     @schema.validator()
        ...     def validate_date(self, data):
        ...         if data['start_date'] > data['end_date']:
        ...             raise schema.ValidationError('开始日期不能大于结束日期')

        >>> MySchema().deserialize({'start_date': '2000-01-01', 'end_date': '1999-01-01'})
        Traceback (most recent call last):
            ...
        django_openapi_schema.exceptions.ValidationError: {'msgs': ['开始日期不能大于结束日期']}

    :param field: 字段或字段名，将校验函数应用于该字段。

        .. code-block::
            :emphasize-lines: 7

            >>> from django_openapi import schema

            >>> class Person(schema.Model):
            ...     name = schema.String()
            ...     age = schema.Integer()
            ...
            ...     @schema.validator(age)
            ...     def validate_age(self, value):
            ...         if value < 0:
            ...             raise schema.ValidationError('年龄不能小于0')

            >>> Person().deserialize({'name': '张三', 'age': -1})
            Traceback (most recent call last):
                ...
            django_openapi_schema.exceptions.ValidationError: {'fields': [{'loc': ['age'], 'msgs': ['年龄不能小于0']}]}
    """

    def decorator(method, field=None):
        return set_hook(
            method,
            lambda: (
                "validator",
                field._name if isinstance(field, Schema) else field,
            ),
        )

    if inspect.isfunction(__a):
        return decorator(__a)
    return functools.partial(decorator, field=__a)
