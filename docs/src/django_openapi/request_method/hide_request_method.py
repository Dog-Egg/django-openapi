from django_openapi import Resource, Operation


@Resource("/to/path")
class API:
    def get(self):
        pass

    @Operation(include_in_spec=False)  # delete 方法将不会被解析到 OAS 中
    def delete(self):
        pass
