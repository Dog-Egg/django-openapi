# 从零开始

## 创建一个 Django 项目

```bash
pip install django # 安装 Django

django-admin startproject myproject # 初始化项目

cd myproject
python manage.py startapp books # 初始化一个 books 应用
```

我们将得到以下的目录结构

```
myproject
├── books
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── migrations
│   │   └── __init__.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── manage.py
└── myproject
    ├── __init__.py
    ├── asgi.py
    ├── settings.py
    ├── urls.py
    └── wsgi.py
```

_更多项目创建说明查看 [Django 文档](https://docs.djangoproject.com/zh-hans/4.0/intro/tutorial01/)_

## 安装 Django-OpenAPI

```bash
pip install git+https://github.com/Dog-Egg/django-openapi.git
```