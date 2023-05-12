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
