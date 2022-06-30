from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=50)
    birthday = models.DateField()


class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
