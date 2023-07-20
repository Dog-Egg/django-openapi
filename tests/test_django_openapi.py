import re

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile

from django_openapi import Resource, schema
from django_openapi.parameter.parameters import Body


def test_Resource_path():
    with pytest.raises(
        ValueError,
        match=re.escape('The path must start with a "/"'),
    ):
        Resource("to/path")


def test_Body_upload_file(rf):
    """单文件上传，Content-Type: multipart/form-data"""
    req = rf.post(
        "/upload",
        {
            "file": SimpleUploadedFile(
                "image.png", b"file_content", content_type="image/png"
            )
        },
    )

    file = Body(
        {"file": schema.File()}, content_type="multipart/form-data"
    ).parse_request(req)["file"]
    assert isinstance(file, UploadedFile)
    assert file.name == "image.png"
    assert file.read() == b"file_content"


def test_Body_upload_mulitple_files(rf):
    """多文件上传，Content-Type: multipart/form-data"""
    req = rf.post(
        "/upload",
        {
            "file": [
                SimpleUploadedFile(
                    "image.png", b"file_content", content_type="image/png"
                )
            ]
            * 2
        },
    )

    files = Body(
        {
            "file": schema.List(schema.File),
        },
        content_type="multipart/form-data",
    ).parse_request(req)["file"]
    assert isinstance(files, list)
    assert len(files) == 2
    assert all(isinstance(i, UploadedFile) for i in files)


def test_Body_multiple_content_types(rf):
    """测试请求体同时支持多个 Content-Type"""

    body = Body(
        {
            "username": schema.String(),
            "password": schema.Password(),
        },
        content_type=[
            "multipart/form-data",
            "application/json",
        ],
    )

    # form-data
    req = rf.post(
        "/",
        data={"username": "username", "password": "pwd"},
    )
    assert body.parse_request(req) == {"username": "username", "password": "pwd"}

    # json
    assert body.parse_request(
        rf.post(
            "/",
            {"username": "username", "password": "pwd"},
            content_type="application/json",
        )
    ) == {"username": "username", "password": "pwd"}
