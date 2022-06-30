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

openapi = OpenAPI()
openapi.add_router('books', views.BooksAPI)
openapi.add_router('books/<int:book_id>', views.BookAPI)
openapi.add_router('authors', views.AuthorAPI)

urlpatterns = [
    path('', openapi.swagger_ui),
    path('api/', openapi.urls),
    path('admin/', admin.site.urls),
]
