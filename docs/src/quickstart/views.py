from django_openapi import Resource


@Resource("/greeting")
class GreetingAPI:
    def get(self):
        return "Hello World"
