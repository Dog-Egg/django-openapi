import json
import os
from string import Template

from django import setup
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder

settings.configure(
    INSTALLED_APPS=[
        'django.contrib.auth',
        'django.contrib.contenttypes',
    ]
)
setup()

from app import openapi
from django.test.client import RequestFactory

request = RequestFactory().get('/api/apispec-12345678')
spec = json.dumps(openapi.get_spec(request), cls=DjangoJSONEncoder)

if __name__ == '__main__':
    with open(os.path.join(os.path.dirname(__file__), 'swagger-ui-template.html')) as fp:
        s = Template(fp.read())
        with open(os.path.join(os.path.dirname(__file__), '../_static/_demo.html'), mode='w') as fp2:
            fp2.write(
                '<!--这是由 demo/main.py 生成的文件-->\n' +
                s.substitute(spec=spec)
            )
