"""混合类型"""
import pytest

from django_openapi import Operation
from django_openapi.parameters import Body
from django_openapi.schema import schemas
from django_openapi.schema.exceptions import ValidationError
from django_openapi.schema.schemas import OneOf, AnyOf
from django_openapi.urls import reverse
from tests.utils import TestResource


class Dog(schemas.Model):
    bark = schemas.Boolean()
    breed = schemas.String(choices=['Dingo', 'Husky', 'Retriever', 'Shepherd'])


class Cat(schemas.Model):
    hunts = schemas.Boolean()
    age = schemas.Integer()


@TestResource
class API:
    one_of = OneOf(Cat, Dog)

    @staticmethod
    @Operation(response_schema=one_of)
    def put(body=Body(one_of)):
        return body


def test_oneof_correct(client):
    resp = client.put(reverse(API), data={
        "bark": True,
        "breed": "Dingo"
    }, content_type='application/json')
    assert resp.json() == {"bark": True, "breed": "Dingo"}


def test_oneof_incorrect(client):
    resp = client.put(reverse(API), data={
        "bark": True,
        "hunts": True,
    }, content_type='application/json')
    assert resp.json() == {'errors': ['no schema is matched.']}


def test_oneof_incorrect_2(client):
    resp = client.put(reverse(API), data={
        "bark": True,
        "hunts": True,
        "breed": "Husky",
        "age": 3
    }, content_type='application/json')
    assert resp.json() == {'errors': ['multiple schemas were matched.']}


class PetByAge(schemas.Model):
    age = schemas.Integer()
    nickname = schemas.String(required=False)


class PetByType(schemas.Model):
    pet_type = schemas.String(choices=['Dog', 'Cat'])
    hunts = schemas.Boolean(required=False)


@TestResource
class API2:
    @staticmethod
    def patch(body=Body(AnyOf(PetByAge, PetByType))):
        return body


@pytest.mark.parametrize('data,result', [
    ({"age": 1}, {"age": 1}),
    ({"pet_type": "Cat", "hunts": True, }, {"pet_type": "Cat", "hunts": True, }),
    ({"nickname": "Fido", "pet_type": "Dog", "age": 4}, {'age': 4, 'nickname': 'Fido'})
])
def test_anyof_correct(client, data, result):
    resp = client.patch(reverse(API2), data, content_type='application/json')
    assert resp.json() == result


def test_anyof_incorrect(client):
    resp = client.patch(reverse(API2), data={
        "nickname": "Mr. Paws",
        "hunts": False
    }, content_type='application/json')
    assert resp.json() == {'errors': ['no schema is matched.']}


def test_discriminator():
    anyof = AnyOf(Cat, Dog, discriminator=schemas.Discriminator('pet_type', {
        'Cat': Cat,
        'Dog': Dog,
    }))

    with pytest.raises(ValidationError, match="""^'pet_type' is required.$"""):
        anyof.deserialize({})

    assert anyof.deserialize({'pet_type': 'Dog', 'bark': True, 'breed': 'Dingo'}) == {'bark': True, 'breed': 'Dingo'}
    assert anyof.serialize({'pet_type': 'Dog', 'bark': True, 'breed': 'Dingo'}) == {'bark': True, 'breed': 'Dingo'}

    with pytest.raises(ValidationError, match="^pet_type='Pet' dose not match the discriminator mapping.$"):
        assert anyof.deserialize({'pet_type': 'Pet'})

    with pytest.raises(ValidationError, match="^pet_type='Pet' dose not match the discriminator mapping.$"):
        assert anyof.serialize({'pet_type': 'Pet'})


@TestResource
class API3:
    class Schema(schemas.Model):
        tag = schemas.AnyOf(
            schemas.Integer,
            schemas.String,
            alias='Tag',
            description='标签'
        )

    @staticmethod
    def post(body=Body(Schema)):
        return body


def test_api3(client):
    resp = client.post(reverse(API3), data={'Tag': '1'}, content_type='application/json')
    assert resp.json() == {'tag': 1}
