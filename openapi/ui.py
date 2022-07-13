from django.shortcuts import render
from django.urls import reverse


def swagger_ui(viewname, title=None):
    title = ('%s | SwaggerUI' % title) if title else 'SwaggerUI'

    def view(request):
        url = request.build_absolute_uri(reverse(viewname))
        return render(request, 'swagger-ui.html', context=dict(url=url, title=title))

    return view


def redoc(viewname, title=None):
    title = ('%s | Redoc' % title) if title else 'Redoc'

    def view(request):
        url = request.build_absolute_uri(reverse(viewname))
        return render(request, 'redoc.html', context=dict(url=url, title=title))

    return view
