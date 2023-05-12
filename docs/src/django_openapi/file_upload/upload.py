from django_openapi import Resource, schema
from django_openapi.parameter import Body


@Resource("/uploadFile")
class UploadAPI:
    def post(
        self,
        file=Body(
            {
                "file": schema.File(),
            },
            content_type="multipart/form-data",
        ),
    ):
        ...
