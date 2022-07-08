from setuptools import setup, find_packages

setup(
    name='django-openapi',
    version='0.0.1',
    packages=find_packages(include=['openapi', 'openapi.*']),
    python_requires='>=3.7',
    author='Lee',
    author_email='294622946@qq.com',
    url='https://github.com/Dog-Egg/django-openapi',
)
