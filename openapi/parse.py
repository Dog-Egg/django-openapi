import re
import typing

from openapi.core import API, Operation
from openapi.globals import openapi
from openapi.spec.schema import ParameterObject, SchemaObject, PathItemObject


def parse_route_and_api_cls(*, route, api_cls: typing.Type[API]):
    operations = {}
    openapi_path, route_params = parse_route(route)

    for method in api_cls.HTTP_METHODS:
        handler = getattr(api_cls, method, None)
        if not handler:
            continue

        op = Operation.manager.get(handler, Operation())
        op_spec = op.to_spec()
        op_spec.tags.extend(api_cls.tags)
        op_spec.parameters.extend(route_params)
        operations[method] = op_spec

    openapi.paths[openapi_path] = PathItemObject(**operations)


def parse_route(route: str):
    converter_to_type = {
        'int': SchemaObject.TypeEnum.INTEGER
    }

    pattern = re.compile(r"<(?:(?P<converter>[^>:]+):)?(?P<parameter>[^>]+)>")
    params = []
    openapi_path = route
    for match in pattern.finditer(route):
        converter, parameter = match.groups()
        params.append(ParameterObject(
            name=parameter,
            in_=ParameterObject.InEnum.PATH,
            required=True,
            schema=SchemaObject(type=converter_to_type.get(converter, None))
        ))
        openapi_path = route.replace(match.group(), '{%s}' % parameter)

    if not openapi_path.startswith('/'):
        openapi_path = '/' + openapi_path
    return openapi_path, params
