"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from openapi.core import OpenAPI
from openapi.views import swagger_ui
from openapi.parameters import Path

from .views import Auth
from library import views
from library.views import BookSchema

openapi = OpenAPI(title='This is example')
openapi.add_route('/books', views.BooksAPI)
openapi.add_route(Path('/books/{book_id}', book_id=BookSchema.id), views.BookAPI)
openapi.add_route('/authors', views.AuthorAPI)
openapi.add_route('/auth', Auth)

urlpatterns = [
    path('', openapi.urls),
    path('api-spec', openapi.api_spec, name='api-spec'),
    path('', swagger_ui('api-spec')),

    path('admin/', admin.site.urls),
]
