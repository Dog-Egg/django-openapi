from django.http import JsonResponse
from openapi.core import API


class BooksAPI(API):
    def get(self, request):
        return JsonResponse({})
