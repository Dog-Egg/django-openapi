"""下载 SwaggerUI 的依赖文件到 static 目录"""
import argparse
import os.path

import requests

URLS = [
    "https://unpkg.com/swagger-ui-dist@{version}/swagger-ui.css",
    "https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-bundle.js",
    "https://unpkg.com/swagger-ui-dist@{version}/swagger-ui-standalone-preset.js",
]


def main(version):
    dirname = os.path.realpath(
        os.path.join(
            os.path.dirname(__file__),
            f"../src/django_openapi/templates/_static/",
        )
    )

    os.makedirs(dirname, exist_ok=True)
    for url in URLS:
        url = url.format(version=version)
        response = requests.get(url)
        filename = os.path.join(dirname, os.path.basename(url))
        with open(filename, "wb") as fp:
            fp.write(response.content)
            print("Successful download %r" % filename)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下载 SwaggerUI 的依赖文件到 static 目录")
    parser.add_argument("version")
    args = parser.parse_args()
    main(args.version)
