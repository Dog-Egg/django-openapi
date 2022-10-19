from django_openapi import Resource, Operation
from django_openapi.schema import schemas


@Resource('/foo')
class A:
    class Schema1(schemas.Model):
        """doc 1"""

    class Schema2(schemas.Model):
        """doc 2"""

        class Meta:
            register_as_component = False

    def __init__(self, *args, **kwargs):
        pass

    @Operation(
        summary='测试 schemas.Model description 展示优先级',
        response_schema=dict(
            s11=Schema1(description='desc 1'),
            s12=Schema1(),
            s21=Schema2(description='desc 2'),
            s22=Schema2(),
        )
    )
    def get(self):
        pass
