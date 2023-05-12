from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/uploadFields")
class UploadFieldsAPI:
    def post(
        self,
        body=Body(
            {
                "file": schema.List(schema.File),
            },
            content_type="multipart/form-data",
        ),
    ):
        ...
