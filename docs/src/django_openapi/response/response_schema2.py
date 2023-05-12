from dataclasses import dataclass

from django_openapi import Operation, Resource, schema


@dataclass
class Student:
    name: str
    age: int


@Resource("/to/path")
class API:
    @Operation(
        response_schema={
            "name": schema.String(),
            "age": schema.Integer(),
        }
    )
    def get(self):
        return Student(name="李华", age=12)
