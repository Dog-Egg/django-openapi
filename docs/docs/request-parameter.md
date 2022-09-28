# 请求参数

## 路径参数

```python
from openapi import Resource

# highlight-next-line
@Resource('/my-api/{some_id}')
class MyAPI:
    # highlight-next-line
    def get(self, request, some_id):
        # do something...
```

```python
from openapi import Resource
from openapi.schema import schemas

# highlight-next-line
@Resource('/my-api/{some_id}', parameters={'some_id': schemas.Integer()})
class MyAPI:
    # highlight-next-line
    def get(self, request, some_id):
        # do something...
```

## Query 参数

使用 [`Query`](#) 来声明一个请求的 query 参数

使用方式如同定义一个关键字参数，django-openapi 能识别并在请求时传入实际参数

```python
from openapi import Resource
from openapi.parameters import Query
from openapi.schema import schemas

class SearchSchema(schemas.Model):
    # 定义 search 的参数结构
    name = schemas.String(description='名称', required=False)
    status = schemas.Integer(description='状态', required=False)

@Resource('/my-api')
class MyAPI:
    # highlight-next-line
    def get(self, request, search=Query(SearchSchema)):
        # do something...
```

如 `?name=foo&status=1&xx=...` 将得到 `search = {'name': 'foo', 'status': 1}`

### 空白值

很多时候客户端可能会传入空白值，如 `?name=&status=`，schemas.Model 反序列时默认忽略空白值的字段，解析结果将是 `search = {}`

schema 参数 `allow_blank` 用来控制空白值输入，如果需要接收空白值，设置 `allow_blank=True`，默认值 False

### Query 参数

`Query` 只允许传入 `schema.Model`，但是为了方便，也可以传入一个字典形式的 Model

```python
@Resource('/my-api')
class MyAPI:
    # 等同于上面的写法
    # highlight-start
    def get(self, request, query=Query({
        'name': schemas.String(description='名称', required=False),
        'status': schemas.Integer(description='状态', required=False)
    })):
    # highlight-end
        # do something...
```

### 多个 Query

Query 可以同时定义多个，如果说上面的 search 用来实现查询，那么可以再定义一个 pagination 来处理分页的参数

```python
# ...

class PaginationSchema(schemas.Model):
    page = schemas.Integer(default=1, gte=1)
    page_size = schemas.Integer(default=100, gte=10, lte=500)

@Resource('/my-api')
class MyAPI:
    # highlight-next-line
    def get(self, request, search=Query(SearchSchema), pagination=Query(PaginationSchema)):
        # do something...
```

请求参数 `?name=foo&status=1&page=2` 将得到:

`search = {'name': 'foo', 'status': 1}` 和 `pagination = {'page': 2, 'page_size': 100}`

## Cookie 参数

`openapi.parameters.Cookie`，使用方式如 [Query](#query)，不同点在于它从 request cookie 里解析参数

## Header 参数

`openapi.parameters.Header`，使用方式如 [Query](#query)，不同点在于它从 request header 里解析参数
