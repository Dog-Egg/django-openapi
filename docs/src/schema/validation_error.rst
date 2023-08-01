校验失败
========

无论数据的结构有多复杂，Schema 总能在反序列化失败时准确地描述出数据出错的消息和位置。

.. testcode::

    import pprint
    from django_openapi import schema

    class Student(schema.Model):
        """学生"""
        name = schema.String()
        age = schema.Integer()

        @schema.validator(age)
        def validate_age(self, value):
            if value <= 0:
                raise schema.ValidationError('The age cannot be less than 0.')

    class Grade(schema.Model):
        """年级"""
        students = schema.List(Student)

    class School(schema.Model):
        """学校"""
        name = schema.String()
        grades = schema.Dict(Grade)

    try:
        School().deserialize({
            'name': '第四小学',
            'grades': {
                '一年级': {
                    'students': [
                        {'name': '小明', 'age': -8},
                        {'name': '小红', 'age': 8},
                    ]
                },
                '二年级': {
                    'students': [
                        {'name': '李华', 'age': 8},
                        {'name': '李子明', 'age': 'a'}
                    ]
                }
            }
        })
    except schema.ValidationError as e:
        pprint.pprint(e.format_errors())

运行上面的代码将得到以下结果，这段数据中存在 2 个错误。

.. testoutput::

    [{'loc': ['grades', '一年级', 'students', 0, 'age'],
      'msgs': ['The age cannot be less than 0.']},
     {'loc': ['grades', '二年级', 'students', 1, 'age'],
      'msgs': ['Not a valid integer.']}]

``loc`` 指明数据错误的位置，它是一个列表，其元素依次引导递进的位置。

``msgs`` 提供数据错误的消息，它是一个列表，当数据未通过多个验证器时会得到多条消息。


自定义错误消息
--------------

.. testcode::

    class Foo(schema.Model):
        a = schema.String()
        b = schema.String(error_messages={'required': '字段 b 是必需的。'})

    try:
        Foo().deserialize({})
    except schema.ValidationError as e:
        pprint.pprint(e.format_errors())

.. testoutput::

    [{'loc': ['a'], 'msgs': ['This field is required.']},
     {'loc': ['b'], 'msgs': ['字段 b 是必需的。']}]


.. note::
    消息可以不只是字符串，它可以是任意对象。

.. testcode::

    class Foo(schema.Model):
        a = schema.String(error_messages={
                "required": {
                    "code": 1001,
                    "err": "This value is required.",
                }
            })

    try:
        Foo().deserialize({})
    except schema.ValidationError as e:
        pprint.pprint(e.format_errors())

.. testoutput::

    [{'loc': ['a'], 'msgs': [{'code': 1001, 'err': 'This value is required.'}]}]


覆盖默认的错误消息
^^^^^^^^^^^^^^^^^^^

使用上下文的方式来覆盖默认的错误消息的。


.. testcode::

    class Foo(schema.Model):
        a = schema.String()

    with schema.error_message_context({
        'required': '这是一个必需字段。'
    }):
        try:
            Foo().deserialize({})
        except schema.ValidationError as e:
            pprint.pprint(e.format_errors())

.. testoutput::

    [{'loc': ['a'], 'msgs': ['这是一个必需字段。']}]


默认错误消息键值参考
--------------------

.. literalinclude:: ../../../src/django_openapi_schema/_error_messages.py