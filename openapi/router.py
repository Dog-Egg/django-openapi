import typing

from django.shortcuts import render
from django.urls import path
from django.http import JsonResponse

from openapi.core import API
from openapi.globals import openapi
from openapi.parse import parse_route_and_api_cls


def doc_view(request):
    return render(request, 'swagger-ui.html')


class Router:
    def __init__(self):
        self._urls = [
            path('doc', doc_view),
            path('spec', self._get_spec)
        ]

    @staticmethod
    def _get_spec(_):
        return JsonResponse(openapi.serialize())

    def add(self, route, api_cls: typing.Type[API]):
        parse_route_and_api_cls(route=route, api_cls=api_cls)
        self._urls.append(path(route, api_cls.as_view()))

    @property
    def urls(self):
        return [self._urls, None, None]
