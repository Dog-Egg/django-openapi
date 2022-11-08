from django_openapi.spec.utils import clean_commonmark, Skip
from django_openapi.utils.datastructures import ImmutableDict


class Tag(ImmutableDict):
    def __init__(self, name: str, description: str = None, external_docs: 'ExternalDocs' = None):
        super().__init__(name=name, description=clean_commonmark(description), externalDocs=external_docs)

    @property
    def name(self):
        return self['name']


class ExternalDocs(ImmutableDict):
    def __init__(self, url: str, description: str = None):
        super().__init__(url=url, description=clean_commonmark(description))


class Example(ImmutableDict):
    def __init__(self, value, *, summary: str = None, description: str = None):
        super().__init__(
            value=Skip(value),
            summary=summary,
            description=clean_commonmark(description)
        )
