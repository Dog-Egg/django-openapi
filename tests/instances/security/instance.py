from tests.utils import TestOpenAPI

openapi = TestOpenAPI(
    title='安全表述',
    description="""
    测试全局验证和 Operation 验证同时存在
    """,
    security=[{}, {'from': []}],  # 全局
    security_schemes={
        'from': {
            'type': 'apiKey',
            'name': 'x-from',
            'in': 'header',
        },
        'token': {
            'type': 'apiKey',
            'name': 'sessionid',
            'in': 'cookie',
        }
    }
)
openapi.find_resources(__package__)
