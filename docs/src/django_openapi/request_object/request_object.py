from django.http import HttpRequest

from django_openapi import Resource


@Resource("/to/path")
class API:
    def __init__(self, request):
        assert isinstance(request, HttpRequest)

    def get(self):
        ...
