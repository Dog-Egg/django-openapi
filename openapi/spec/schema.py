import enum
import typing
from http import HTTPStatus

__version__ = '3.0.3'


class _Serializable:

    def _serialize(self):
        raise NotImplementedError

    def serialize(self):
        spec = self._serialize()
        if isinstance(spec, dict):
            _spec = {}
            for name, value in spec.items():
                if isinstance(value, _Serializable):
                    value = value.serialize()
                elif isinstance(value, list):
                    value = [x.serialize() if isinstance(x, _Serializable) else x for x in value]

                if value is not None:
                    _spec[name] = value
            return _spec
        return spec


class OpenAPIObject(_Serializable):
    def __init__(
            self,
            /,
            info: 'InfoObject',
            paths: 'PathsObject',
            servers: typing.List['ServerObject'] = None,
    ):
        self.openapi = __version__
        self.info = info
        self.paths = paths
        self.servers = servers

    def _serialize(self):
        return {
            'openapi': self.openapi,
            'info': self.info,
            'paths': self.paths,
            'servers': self.servers,
        }


class InfoObject(_Serializable):
    def __init__(
            self,
            /,
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


class PathsObject(_Serializable):
    def __init__(self, paths: typing.Dict[str, 'PathItemObject'], /):
        self._paths = paths

    def _serialize(self):
        return self._paths

    def __setitem__(self, path, item):
        assert isinstance(item, PathItemObject)
        self._paths[path] = item


class PathItemObject(_Serializable):
    def __init__(
            self,
            /,
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
        return {
            'get': self.get,
            'put': self.put,
            'post': self.post,
            'delete': self.delete,
            'options': self.options,
            'head': self.head,
            'patch': self.patch,
            'trace': self.trace,
        }


class OperationObject(_Serializable):
    def __init__(
            self,
            /,
            responses: 'ResponsesObject',
            tags: typing.List[str] = None,
            summary: str = None,
            description: str = None,
            parameters: typing.List['ParameterObject'] = None,
            request_body: 'RequestBodyObject' = None,
    ):
        self.tags = tags
        self.summary = summary
        self.description = description
        self.parameters = parameters
        self.responses = responses
        self.request_body = request_body

    def _serialize(self):
        return {
            'tags': self.tags,
            'summary': self.summary,
            'description': self.description,
            'parameters': self.parameters,
            'requestBody': self.request_body,
            'responses': self.responses,
        }


class ResponsesObject(_Serializable):
    HTTP_STATUS_SET = set(e.value for e in HTTPStatus)

    def __init__(self, responses: typing.Dict[str, 'ResponseObject'], /):
        # assert responses
        # for code, res in responses.items():
        #     assert code == 'default' or (code.isdigit() and int(code) in self.HTTP_STATUS_SET)
        self.responses = responses

    def _serialize(self):
        return self.responses


class ResponseObject(_Serializable):
    def __init__(
            self,
            /,
            description: str
    ):
        self.description = description

    def _serialize(self):
        return {
            'description': self.description
        }


class ParameterObject(_Serializable):
    class InEnum(_Serializable, enum.Enum):
        QUERY = 'query'
        HEADER = 'header'
        PATH = 'path'
        COOKIE = 'cookie'

        def _serialize(self):
            return self.value

    def __init__(
            self,
            /,
            name: str,
            in_: InEnum,
            description: str = None,
            required: bool = None,
            deprecated: bool = None,
            schema: 'SchemaObject' = None,
            example=None
    ):
        if in_ == self.InEnum.PATH and not required:
            raise ValueError(
                'If the parameter location is "path", this property is REQUIRED and its value MUST be true.')

        self.name = name
        self.in_ = in_
        self.description = description
        self.required = required
        self.deprecated = deprecated
        self.schema = schema
        self.example = example

    def _serialize(self):
        return {
            'name': self.name,
            'in': self.in_,
            'required': self.required,
            'schema': self.schema,
            'description': self.description,
            'example': self.example,
        }


class SchemaObject(_Serializable):
    class TypeEnum(_Serializable, enum.Enum):
        INTEGER = 'integer'
        STRING = 'string'

        def _serialize(self):
            return self.value

    # noinspection PyShadowingBuiltins
    def __init__(
            self,
            /,
            type: TypeEnum = None,
            default=None
    ):
        self.type = type
        self.default = default

    def _serialize(self):
        return {
            'type': self.type,
            'default': self.default
        }


class ServerObject(_Serializable):
    def __init__(self, /, url: str, description: str = None):
        self.url = url
        self.description = description

    def _serialize(self):
        return {
            'url': self.url,
            'description': self.description,
        }


class RequestBodyObject(_Serializable):
    def __init__(self, *, content: typing.Dict[str, 'MediaTypeObject'], description: str = None, required: bool = None):
        self.content = content
        self.description = description
        self.required = required

    def _serialize(self):
        return {
            'content': self.content,
            'description': self.description,
            'required': self.required,
        }


class MediaTypeObject(_Serializable):
    def __init__(self, *, schema: SchemaObject = None, example=None):
        self.schema = schema
        self.example = example

    def _serialize(self):
        return {
            'schema': self.schema,
            'example': self.example,
        }


if __name__ == '__main__':
    import pprint

    pprint.pprint(OpenAPIObject(
        info=InfoObject(title='This is title'),
        paths=PathsObject({'/api/a': PathItemObject(
            get=OperationObject(
                parameters=[
                    ParameterObject(name='arg1', in_=ParameterObject.InEnum.QUERY,
                                    schema=SchemaObject(type=SchemaObject.TypeEnum.INTEGER))],
                responses=ResponsesObject({
                    '200': ResponseObject(description='description1')
                })
            )
        )})
    ).serialize())
