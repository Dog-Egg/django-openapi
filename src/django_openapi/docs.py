import hashlib
import typing
from collections import defaultdict

from django.http import HttpRequest, HttpResponse, HttpResponseNotModified
from django.template.loader import render_to_string
from django.urls import reverse_lazy

from django_openapi import OpenAPI


def _get_swagger_ui_html(config: dict, insert_head="", env=None):
    return render_to_string(
        "swagger-ui.html",
        context=dict(
            config=config,
            insert_head=insert_head,
            env=env,
        ),
    )


def swagger_ui(*openapi: OpenAPI):
    name_to_oas: typing.Dict[str, typing.List[OpenAPI]] = defaultdict(list)
    for oa in openapi:
        name_to_oas[oa.title].append(oa)

    urls = []
    for name, oas in name_to_oas.items():
        for i, oa in enumerate(oas):
            if i:
                name = "%s(%s)" % (name, i)
            urls.append(dict(name=name, url=reverse_lazy(oa.spec_view)))

    def view(request: HttpRequest):
        if not urls:
            config = {}
        elif len(urls) == 1:
            config = {"url": urls[0]["url"]}
        else:
            config = {"urls": urls}

        content = _get_swagger_ui_html(config)

        etag = '"%s"' % hashlib.sha1(content.encode()).hexdigest()
        if request.headers.get("If-None-Match") == etag:
            return HttpResponseNotModified()
        return HttpResponse(content, headers={"ETag": etag})

    return view
