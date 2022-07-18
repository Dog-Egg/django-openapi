from django.db import models
from django.core import validators


class Author(models.Model):
    name = models.CharField(max_length=50)
    birthday = models.DateField()


class Book(models.Model):
    title = models.CharField(max_length=50)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    tag = models.CharField(max_length=20)
    price = models.DecimalField(max_digits=5, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)


class Foo(models.Model):
    char1 = models.CharField(max_length=10, editable=True)
    age = models.IntegerField(verbose_name='年龄', help_text='这是一段描述文字', validators=[validators.MinValueValidator(1)])
    # create_time = models.DateTimeField(verbose_name='创建时间', auto_now_add=True)
