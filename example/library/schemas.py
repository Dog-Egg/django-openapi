from openapi.schemax.exceptions import ValidationError
from openapi.schemax import fields, validators

from . import models


class BookSchema(fields.Schema):
    """图书"""

    class ValidateAuthorID(validators.Validator):
        def validate(self, value) -> None:
            try:
                models.Author.objects.get(pk=value)
            except models.Author.DoesNotExist:
                raise ValidationError('ID不存在')

    id = fields.Integer(description='图书ID', example=1, required=True)
    title = fields.String(description='书名', example='三体', required=True)
    author_id = fields.Integer(description='作者ID', example=1, required=True, validators=[ValidateAuthorID()])
    created_at = fields.Datetime(description='创建时间', required=True)


class AuthorSchema(fields.Schema):
    """作者"""
    id = fields.Integer(description='作者ID', example=1, required=True)
    name = fields.String(description='作者姓名', example='刘慈溪', required=True, strip=True)
    birthday = fields.Date(description='生日', required=True)
