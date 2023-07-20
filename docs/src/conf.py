import os
import sys

sys.path.extend(
    [
        os.path.abspath("./_ext"),
        os.path.abspath("../../src"),
        os.path.abspath("../"),
    ]
)

# Project information
project = "Django-OpenAPI"

# General configuration
extensions = [
    "openapiview",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autodoc",
    "sphinx.ext.doctest",
]
default_role = "py:obj"
rst_epilog = """
.. |OAS| replace:: `OpenAPI Specification <https://spec.openapis.org/oas/v3.0.3>`__
"""
nitpicky = True
nitpick_ignore = [
    ("py:class", "re.Pattern"),
    ("py:class", "django.db.models.query.QuerySet"),
    ("py:class", "django_openapi.parameter.parameters.RequestParameter"),
]

# HTML output
html_theme = "furo"
html_static_path = ["_static"]


# internationalization
language = "zh_CN"

# Extension intersphinx
intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# Extension autodoc
autodoc_typehints = "description"
autodoc_typehints_description_target = "documented_params"
