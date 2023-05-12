SECRET_KEY = "testing"
ROOT_URLCONF = "tests.urls"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "mydatabase",
    }
}

INSTALLED_APPS = [
    "tests",
    "docs.src.django_openapi.pagination",
    "docs.src.examples",
]

USE_TZ = True
