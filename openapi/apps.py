from django.apps import AppConfig
from django.urls import register_converter, converters


class OpenAPIConfig(AppConfig):
    name = 'openapi'


register_converter(converters.PathConverter, 'openapi')
