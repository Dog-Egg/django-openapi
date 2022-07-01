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

from library import views
from openapi.core import OpenAPI
from .views import Auth

openapi = OpenAPI(title='This is example')
openapi.add_route('books', views.BooksAPI) \
    .add_route('{book_id}', views.BookAPI)
openapi.add_route('authors', views.AuthorAPI)
openapi.add_route('auth', Auth)

urlpatterns = [
    path('', openapi.swagger_ui),
    path('', openapi.urls),
    path('api-spec', openapi.get_spec),
    path('admin/', admin.site.urls),
]
