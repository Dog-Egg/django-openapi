import importlib.util
import os
import traceback
import uuid
from html import escape

import django
import jinja2
from django.apps import apps
from django.conf import settings
from docutils import nodes
from docutils.parsers.rst import Directive, directives
from jinja2 import Template

with open(os.path.join(os.path.dirname(__file__), "swagger-ui.j2")) as fp:
    template = Template(fp.read())

template.environment.policies["json.dumps_kwargs"] = {"sort_keys": False}


class OpenAPIView(Directive):
    has_content = True
    option_spec = {
        "docexpansion": directives.unchanged,
        "defaultmodelrendering": directives.unchanged,
    }

    def run(self):
        try:
            filename = self.state.document.settings.env.relfn2path(self.content[0])[1]
            module = import_module_from_file(filename)

            oas = parse_module(module)
            html = template.render(spec=oas, options=self.options)

            iframe_id = "id_" + uuid.uuid4().hex[:8]
            html = f"""
            <iframe id="{iframe_id}" srcdoc="{escape(html)}" frameborder="0" style="border: 1px solid #ddd; min-width: 100%;"></iframe>
            <script src="/_static/iframeResizer.min.js"></script>
            <script>
                iFrameResize({{checkOrigin: false}}, '#{iframe_id}')
            </script>
            """

            node = nodes.raw(text=html, format="html")
            return [node]
        except Exception as exc:
            traceback.print_exc()
            return [self.state.document.reporter.warning(exc, line=self.lineno)]


def parse_module(module):
    """添加模块内的 Resource 对象，解析为 OpenAPI Specification"""
    from devtools import get_openapi_from_module

    openapi = get_openapi_from_module(module)
    oas = openapi.get_spec()
    return oas


def import_module_from_file(path):
    """将文件导入为模块"""
    name = os.path.splitext(os.path.relpath(path, os.getcwd()))[0].replace("/", ".")

    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)

    # 将该模块所在的上级模块注册为 Django APP
    INSTALLED_APPS = [
        module.__name__.rsplit(".", 1)[0],
    ]
    apps.set_installed_apps(INSTALLED_APPS)

    spec.loader.exec_module(module)
    return module


def setup(app):
    settings.configure(INSTALLED_APPS=[])
    django.setup()

    app.add_directive("openapiview", OpenAPIView)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
