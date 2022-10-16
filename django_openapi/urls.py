from django.urls import reverse as _reverse
from django.utils.functional import lazy

from django_openapi import Resource

__all__ = ('reverse', 'reverse_lazy')


def reverse(viewname, *args, **kwargs):
    if isinstance(viewname, Resource):
        viewname = viewname.view
    return _reverse(viewname, *args, **kwargs)


reverse_lazy = lazy(reverse, str)
