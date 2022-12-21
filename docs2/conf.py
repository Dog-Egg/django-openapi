import os.path
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import django_openapi

html_static_path = ['_static']

project = 'Django-OpenAPI'
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

html_theme = 'furo'
html_title = project

language = 'zh_CN'

autodoc_member_order = 'groupwise'

version = django_openapi.__version__
