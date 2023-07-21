import hashlib
import typing
from collections import defaultdict

from django.http import HttpRequest, HttpResponse, HttpResponseNotModified
from django.template.loader import render_to_string
from django.urls import reverse_lazy

from django_openapi import OpenAPI


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
        content = render_to_string(
            "swagger-ui.html", context=dict(urls=urls), request=request
        )
        etag = '"%s"' % hashlib.sha1(content.encode()).hexdigest()
        if request.headers.get("If-None-Match") == etag:
            return HttpResponseNotModified()
        return HttpResponse(content, headers={"ETag": etag})

    return view
