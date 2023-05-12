import typing
from collections import defaultdict

from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils.datastructures import OrderedSet

from django_openapi import OpenAPI


def swagger_ui(*openapi: OpenAPI):
    name_to_oas: typing.Dict[str, typing.List[OpenAPI]] = defaultdict(list)
    for oa in OrderedSet(openapi):
        name_to_oas[oa.title].append(oa)

    urls = []
    for name, oas in name_to_oas.items():
        for i, oa in enumerate(oas):
            if i:
                name = "%s(%s)" % (name, i)
            urls.append(dict(name=name, url=reverse_lazy(oa.spec_view)))

    def view(request):
        return render(
            request,
            "swagger-ui.html",
            context=dict(urls=urls),
        )

    return view
