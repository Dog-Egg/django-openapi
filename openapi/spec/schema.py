import typing
from http import HTTPStatus
from collections import OrderedDict

from openapi.enums import Location, DataType, SecurityType
from openapi.spec._register import ComponentRegistry
from openapi.spec.utils import default_as_none

__version__ = '3.0.3'


class _Object:

    def _serialize(self):
        raise NotImplementedError

    def serialize(self):
        def _filter(obj):
            if isinstance(obj, dict):
                obj = {name: value for name, value in obj.items() if value is not None} or None
            elif isinstance(obj, list):
                obj = [value for value in obj if value is not None] or None
            return obj

        def inner(spec):
            if isinstance(spec, dict):
                return _filter({name: inner(value) for name, value in spec.items()})
            if isinstance(spec, list):
                return _filter([inner(value) for value in spec])
            if isinstance(spec, _Object):
                return inner(spec._serialize())
            return spec

        return inner(self._serialize())


class OpenAPIObject(_Object):
    def __init__(
            self,
            *,
            info: 'InfoObject',
            paths: 'PathsObject',
            servers: typing.List['ServerObject'] = None,
            components: 'ComponentsObject' = None,
            security: typing.List['SecurityRequirementObject'] = None,
    ):
        self.openapi = __version__
        self.info = info
        self.paths = paths
        self.servers = servers
        self.components = components
        self.security = security

    def _serialize(self):
        return {
            'openapi': self.openapi,
            'info': self.info,
            'paths': self.paths,
            'servers': self.servers,
            'components': self.components,
            'security': self.security,
        }


class InfoObject(_Object):
    def __init__(
            self,
            *,
            title: str,
            version: str = '0.1.0'
    ):
        self.title = title
        self.version = version

    def _serialize(self):
        return {
            'title': self.title,
            'version': self.version
        }


class PathsObject(_Object):
    def __init__(self, paths: typing.Dict[str, 'PathItemObject']):
        self._paths = paths

    def _serialize(self):
        return self._paths

    def __setitem__(self, path, item):
        assert isinstance(item, PathItemObject)
        self._paths[path] = item


class PathItemObject(_Object):
    def __init__(
            self,
            *,
            get: 'OperationObject' = None,
            post: 'OperationObject' = None,
            put: 'OperationObject' = None,
            delete: 'OperationObject' = None,
            options: 'OperationObject' = None,
            head: 'OperationObject' = None,
            patch: 'OperationObject' = None,
            trace: 'OperationObject' = None,
    ):
        self.get = get
        self.post = post
        self.put = put
        self.delete = delete
        self.options = options
        self.head = head
        self.patch = patch
        self.trace = trace

    def _serialize(self):
        return OrderedDict([
            ('options', self.options),
            ('get', self.get),
            ('put', self.put),
            ('post', self.post),
            ('delete', self.delete),
            ('head', self.head),
            ('patch', self.patch),
            ('trace', self.trace),
        ])


class OperationObject(_Object):
    def __init__(
            self,
            *,
            responses: 'ResponsesObject',
            tags: typing.List[str] = None,
            summary: str = None,
            description: str = None,
            parameters: typing.List['ParameterObject'] = None,
            request_body: 'RequestBodyObject' = None,
            deprecated: bool = False,
    ):
        self.tags = tags or []
        self.summary = summary
        self.description = description
        self.parameters = parameters
        self.responses = responses
        self.request_body = request_body
        self.deprecated = default_as_none(deprecated, False)

    def _serialize(self):
        return {
            'tags': self.tags,
            'summary': self.summary,
            'description': self.description,
            'parameters': self.parameters,
            'requestBody': self.request_body,
            'responses': self.responses,
            'deprecated': self.deprecated,
        }


class ResponsesObject(_Object):
    HTTP_STATUS_SET = set(e.value for e in HTTPStatus)

    def __init__(self, responses: typing.Dict[typing.Union[str, int], 'ResponseObject']):
        assert responses
        for code, res in responses.items():
            assert code == 'default' or code in self.HTTP_STATUS_SET
        self.responses = responses

    def _serialize(self):
        return self.responses


class ResponseObject(_Object):
    def __init__(
            self,
            *,
            description: str,
            content: typing.Dict[str, 'MediaTypeObject'] = None
    ):
        self.description = description
        self.content = content

    def _serialize(self):
        return {
            'description': self.description,
            'content': self.content
        }


class ParameterObject(_Object):
    def __init__(
            self,
            *,
            name: str,
            location: str,
            description: str = None,
            required: bool = False,
            deprecated: bool = None,
            schema: 'SchemaObject' = None,
            example=None
    ):
        assert location in Location
        if location == Location.PATH and not required:
            raise ValueError(
                'If the parameter location is "path", this property is REQUIRED and its value MUST be true.')

        self.name = name
        self.location = location
        self.description = description
        self.required = default_as_none(required, False)
        self.deprecated = deprecated
        self.schema = schema
        self.example = example

    def _serialize(self):
        return {
            'name': self.name,
            'in': self.location,
            'required': self.required,
            'schema': self.schema,
            'description': self.description,
            'example': self.example,
        }


class SchemaObject(_Object):
    # noinspection PyShadowingBuiltins
    def __init__(self, *, type: str = None, default=None, read_only=False, nullable=False, **kwargs):
        self.type = type
        self.default = default
        self.read_only = default_as_none(read_only, False)
        self.nullable = default_as_none(nullable, False)
        self.kwargs = kwargs

    def extra(self, **kwargs):
        self.kwargs.update(kwargs)

    def _serialize(self):
        return {
            'type': self.type,
            'default': self.default,
            'readOnly': self.read_only,
            **self.kwargs,
        }


class ServerObject(_Object):
    def __init__(self, *, url: str, description: str = None):
        self.url = url
        self.description = description

    def _serialize(self):
        return {
            'url': self.url,
            'description': self.description,
        }


class RequestBodyObject(_Object):
    def __init__(self, *, content: typing.Dict[str, 'MediaTypeObject'], description: str = None, required: bool = None):
        self.content = content
        self.description = description
        self.required = default_as_none(required, False)

    def _serialize(self):
        return {
            'content': self.content,
            'description': self.description,
            'required': self.required,
        }


class MediaTypeObject(_Object):
    def __init__(self, *, schema: typing.Union[SchemaObject, 'ReferenceObject'] = None, example=None):
        self.schema = schema
        self.example = example

    def _serialize(self):
        return {
            'schema': self.schema,
            'example': self.example,
        }


class ReferenceObject(_Object):
    def __init__(self, *, ref: str):
        self.ref = ref

    def _serialize(self):
        return {
            '$ref': self.ref
        }


class ComponentsObject(_Object, ComponentRegistry):
    def __init__(
            self,
            *,
            schemas: typing.Dict[str, SchemaObject] = None,
            responses: typing.Dict[str, ResponseObject] = None,
            security_schemes: typing.Dict[str, 'SecuritySchemeObject'] = None,
    ):
        self.schemas = schemas
        self.responses = responses
        self.security_schemes = security_schemes

    def _serialize(self):
        return {
            'schemas': self.schemas,
            'responses': self.responses,
            'securitySchemes': self.security_schemes,
        }


class SecuritySchemeObject(_Object):
    # noinspection PyShadowingBuiltins
    def __init__(self, *, type, description: str = None, name: str = None, location: str = None):
        assert type in SecurityType
        if type == SecurityType.API_KEY:
            assert all([name, location])

        self.type = type
        self.description = description
        self.name = name
        self.location = location

    def _serialize(self):
        return {
            'type': self.type,
            'description': self.description,
            'name': self.name,
            'in': self.location,
        }


class SecurityRequirementObject(_Object):
    def __init__(self, kwargs: typing.Dict[str, typing.List[str]]):
        self.kwargs = kwargs

    def _serialize(self):
        return self.kwargs


if __name__ == '__main__':
    import pprint

    pprint.pprint(OpenAPIObject(
        info=InfoObject(title='This is title'),
        paths=PathsObject({'/api/a': PathItemObject(
            get=OperationObject(
                parameters=[
                    ParameterObject(name='arg1', location=Location.QUERY,
                                    schema=SchemaObject(type=DataType.INTEGER))],
                responses=ResponsesObject({
                    200: ResponseObject(description='description1')
                }),
                request_body=RequestBodyObject(
                    content={
                        'application/json': MediaTypeObject()
                    }
                )
            )
        )})
    ).serialize())
