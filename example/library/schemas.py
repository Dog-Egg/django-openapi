from openapi.schemax import fields


class BookSchema(fields.Schema):
    """图书"""
    id = fields.Integer(description='图书ID', example=1, required=True)
    title = fields.String(description='书名', example='三体', required=True)
    author = fields.String(description='作者', example='刘慈欣', required=True)
    created_at = fields.Datetime(description='创建时间', required=True)


class AuthorSchema(fields.Schema):
    """作者"""
    id = fields.Integer(description='作者ID', example=1, required=True)
    name = fields.String(description='作者姓名', example='刘慈溪', required=True, strip=True)
    birthday = fields.Date(description='生日', required=True)
