from django_openapi import OpenAPI, Resource

openapi = OpenAPI()


# APP 1
@Resource("/to/path1")
class API1:
    def get(self):
        ...


openapi.add_resource(API1, prefix="/app1", tags=["APP 1"])


# APP 2
@Resource("/to/path2")
class API2:
    def get(self):
        ...


openapi.add_resource(API2, prefix="/app2", tags=["APP 2"])
