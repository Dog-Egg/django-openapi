"""循环引用"""

from django_openapi import Operation
from django_openapi.schema import schemas
from django_openapi.urls import reverse
from tests.utils import TestResource


class TreeNode(schemas.Model):
    """循环引用 Schema"""
    id = schemas.String()
    children = schemas.List(schemas.Ref('TreeNode'))


class Node:
    _id = 0

    def __init__(self, _id, children=None):
        self.id = _id
        self.children = children if children is not None else []


@TestResource
class API:
    @Operation(
        summary='树结构',
        response_schema=dict(root=schemas.List(TreeNode))
    )
    def get(self):
        return {'root': [
            Node(1, children=[Node(2, children=[Node(3), Node(4)]), Node(5)])
        ]}


def test_api(client):
    response = client.get(reverse(API))
    assert response.json() == {'root': [
        {
            'id': '1',
            'children': [
                {
                    'children': [
                        {'children': [], 'id': '3'},
                        {'children': [], 'id': '4'}
                    ],
                    'id': '2'
                },
                {'children': [], 'id': '5'}
            ],
        }]}
