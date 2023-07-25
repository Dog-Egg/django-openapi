from PIL import Image, UnidentifiedImageError

from django_openapi import Operation, Resource, schema
from django_openapi.parameter import Body


@Resource("/uploadImage")
class UploadAPI:
    class PostData(schema.Model):
        file = schema.File()

        @schema.validator(file)
        def validate_image(self, fp):
            """验证文件是否为一个有效图片。"""

            try:
                Image.open(fp)  # 如果不是图片会抛出异常
            except UnidentifiedImageError:
                raise schema.ValidationError("%r不是一个有效的图片。" % fp.name)

    @Operation(summary="上传图片")
    def post(
        self,
        body=Body(
            PostData,
            content_type="multipart/form-data",
        ),
    ):
        ...
