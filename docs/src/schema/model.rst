Model
=====

定义
----

.. code-block::

    >>> from django_openapi import schema

    >>> class Student(schema.Model):
    ...     name = schema.String()
    ...     birthday = schema.Date()

    >>> Student().deserialize({'name': '张三', 'birthday': '2000-03-04'})
    {'name': '张三', 'birthday': datetime.date(2000, 3, 4)}


字段继承
^^^^^^^^

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
^^^^^^

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


无效的字段值
-------------

``invalid_value`` 用于在对字段进行反序列化时，如果输入的字段值被判断为无效值，则会被当成未提供处理。默认的无效值是输入空白字符串。

如下所示字段 a 为必需提供的，虽然反序列化时提供了一个空字符，但默认 ``""`` 是无效的，相当与为提供字段值。

.. testcode::

    class Foo(schema.Model):
        a = schema.String()

    Foo().deserialize({"a": ""})


.. testoutput::

    Traceback (most recent call last):
        ...
    django_openapi_schema.exceptions.ValidationError: [{'msgs': ['This field is required.'], 'loc': ['a']}]
