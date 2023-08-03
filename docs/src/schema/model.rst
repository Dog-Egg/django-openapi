Schema
========

Model
-----

定义
^^^^

.. code-block::

    >>> from django_openapi import schema

    >>> class Student(schema.Model):
    ...     name = schema.String()
    ...     birthday = schema.Date()

    >>> Student().deserialize({'name': '张三', 'birthday': '2000-03-04'})
    {'name': '张三', 'birthday': datetime.date(2000, 3, 4)}


继承
^^^^

.. code-block::
    :caption: 单继承

    >>> class Person(schema.Model):
    ...     name = schema.String()
    ...     birthday = schema.Date()

    >>> class Employee(Person):
    ...     position = schema.String()

    >>> Employee().deserialize({'name': '张三', 'birthday': '2000-03-04', 'position': '产品经理'})
    {'name': '张三', 'birthday': datetime.date(2000, 3, 4), 'position': '产品经理'}


.. code-block::
    :caption: 多继承

    >>> class Person(schema.Model):
    ...     name = schema.String()
    ...     birthday = schema.Date()

    >>> class Employee(schema.Model):
    ...     position = schema.String()

    >>> class MySchema(Person, Employee):
    ...     create_time = schema.Date()

    >>> MySchema().deserialize({'name': '张三', 'birthday': '2000-03-04', 'position': '产品经理', 'create_time': '2023-05-01'})
    {'name': '张三', 'birthday': datetime.date(2000, 3, 4), 'position': '产品经理', 'create_time': datetime.date(2023, 5, 1)}


嵌套
^^^^

.. code-block::

    >>> import pprint

    >>> class Author(schema.Model):
    ...     name = schema.String()
    ...     birthday = schema.Date()

    >>> class Book(schema.Model):
    ...     title = schema.String()
    ...     author = Author()

    >>> pprint.pprint(Book().deserialize({'title': '三体', 'author': {'name': '刘慈欣', 'birthday': '1963-06-23'}}))
    {'author': {'birthday': datetime.date(1963, 6, 23), 'name': '刘慈欣'},
     'title': '三体'}


clear_value
^^^^^^^^^^^

在 ``Model`` 反序列化时，为字段清除无意义的值。

默认定义了空白字符串为无意义值。如下所示: 字段 a 为必需的，虽然反序列化时为其提供了一个空字符，但空字符串默认是无意义的，所以会在处理时被清除。

.. testcode::

    from django_openapi import schema

    class Foo(schema.Model):
        a = schema.String()

    Foo().deserialize({"a": ""})


.. testoutput::

    Traceback (most recent call last):
        ...
    django_openapi_schema.exceptions.ValidationError: [{'msgs': ['This field is required.'], 'loc': ['a']}]

需要为 ``clear_value`` 提供一个函数，函数返回 `True`，则值会被清除；返回 `False` 则不做处理。

.. testcode::

    # 把 0 作为无意义的值处理
    def clear_value(value):
        return value == 0

    class User(schema.Model):
        age = schema.Integer(clear_value=clear_value)

    User().deserialize({'age': 0})

.. testoutput::

    Traceback (most recent call last):
        ...
    django_openapi_schema.exceptions.ValidationError: [{'msgs': ['This field is required.'], 'loc': ['age']}]


将 ``clear_value`` 设为 `None` 可以禁用此设置。

.. testcode::

    class Foo(schema.Model):
        a = schema.String(clear_value=None)

    print(Foo().deserialize({'a': ''}))

.. testoutput::

    {'a': ''}


.. note::
    ``clear_value`` 在对 HTTP 请求处理 Query 参数时很有用。如: ?a=&b=1 转为字典后为 ``{'a': '', 'b': '1'}``，其中 a 参数的空字符串大多数情况下并无意义，所以应当被清除。


前后置处理
----------

deserialization_post
^^^^^^^^^^^^^^^^^^^^

反序列后置处理

.. testcode::

    # 去除字符串前后多余的空白符
    email = schema.String(deserialization_post=str.strip)
    print(repr(email.deserialize('123@example.com  ')))

.. testoutput::

    '123@example.com'