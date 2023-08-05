Schema
========

Model
-----

定义
^^^^

.. testcode::

    import django_openapi_schema as schema

    class Student(schema.Model):
        name = schema.String()
        birthday = schema.Date()

    print(Student().deserialize({'name': '张三', 'birthday': '2000-03-04'}))

.. testoutput::

    {'name': '张三', 'birthday': datetime.date(2000, 3, 4)}


继承
^^^^

.. testcode::

    # 单继承

    class Person(schema.Model):
        name = schema.String()
        birthday = schema.Date()

    class Employee(Person):
        position = schema.String()

    print(Employee().deserialize({
        'name': '张三',
        'birthday': '2000-03-04',
        'position': '产品经理'
    }))

.. testoutput::

    {'name': '张三', 'birthday': datetime.date(2000, 3, 4), 'position': '产品经理'}


.. testcode::

    # 多继承

    from pprint import pprint

    class Person(schema.Model):
        name = schema.String()
        birthday = schema.Date()

    class Employee(schema.Model):
        position = schema.String()

    class MySchema(Person, Employee):
        create_time = schema.Date()

    pprint(MySchema().deserialize({
        'name': '张三',
        'birthday': '2000-03-04',
        'position': '产品经理',
        'create_time': '2023-05-01'
    }))


.. testoutput::

    {'birthday': datetime.date(2000, 3, 4),
     'create_time': datetime.date(2023, 5, 1),
     'name': '张三',
     'position': '产品经理'}


嵌套
^^^^

.. testcode::

    class Author(schema.Model):
        name = schema.String()
        birthday = schema.Date()

    class Book(schema.Model):
        title = schema.String()
        author = Author()

    pprint(Book().deserialize({'title': '三体', 'author': {'name': '刘慈欣', 'birthday': '1963-06-23'}}))

.. testoutput::

    {'author': {'birthday': datetime.date(1963, 6, 23), 'name': '刘慈欣'},
     'title': '三体'}

Field
-----

Field 并不是一种 Schema，只是把作为 Model 字段的 Schema 称为 Field。任意的 Schema 都可直接作为 Model 的字段来使用，包括 Model。以下功能仅在 Schema 作为字段时可用。

clear_value
^^^^^^^^^^^

在 ``Model`` 反序列化时，为字段清除无意义的值。

默认定义了空白字符串为无意义值。如下所示: 字段 a 为必需的，虽然反序列化时为其提供了一个空字符，但空字符串默认是无意义的，所以会在处理时被清除。

.. testcode::

    class Foo(schema.Model):
        a = schema.String()

    Foo().deserialize({"a": ""})


.. testoutput::

    Traceback (most recent call last):
        ...
    django_openapi_schema.exceptions.ValidationError: [{'msgs': ['This field is required.'], 'loc': ['a']}]

自定义时需要为 ``clear_value`` 提供一个函数，函数返回 `True`，则值会被清除；返回 `False` 则不做处理。

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

Schema
------

以下为所有 Schema 通用功能。

deserialization_post
^^^^^^^^^^^^^^^^^^^^

反序列后置处理

.. testcode::

    # 去除字符串前后多余的空白符
    email = schema.String(deserialization_post=str.strip)
    print(repr(email.deserialize('123@example.com  ')))

.. testoutput::

    '123@example.com'


choices
^^^^^^^

为反序列化数据提供可选值。

输入值在选项内:

.. testcode::

    fruit = schema.String(choices=['apple', 'watermelon', 'grape'])

    print(fruit.deserialize('apple'))

.. testoutput::

    apple

输入值不在选项内：

.. testcode::

    fruit.deserialize('banana')

.. testoutput::

    Traceback (most recent call last):
        ...
    django_openapi_schema.exceptions.ValidationError: [{'msgs': ["The value must be one of 'apple', 'watermelon', 'grape'."]}]

