from django.shortcuts import render
from django.urls import reverse


def swagger_ui(viewname):
    def view(request):
        url = request.build_absolute_uri(reverse(viewname))
        return render(request, 'swagger-ui.html', context={'url': url})

    return view
