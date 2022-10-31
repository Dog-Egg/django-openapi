## 0.1a5 (dev)

- 新增：Operation view_decorators
- 更新：Body 提供默认的 schema
- 更新：`@Resource` 只做标记，不修改类本身
- 新增：混合类型 `OneOf` 和 `AnyOf`

## 0.1a4

- 新增：schema BaseSchema 参数 `deserialize_preprocess`, `deserialize_postprocess`
- 新增：schema Datetime 参数 `with_timezone`
- 新增：schema default 参数可以使用函数
- 修复一些BUG

## 0.1a3

- 新增：被 `Resource` 装饰的类可以不定义 `__init__` 方法
- 新增：schema Model 可单独注册，作为文档的一部分
- 新增：url `reverse` 函数
- 新增：schema String 参数 `whitespace`
- 修改：`allow_blank` 仅判断空字符串，而不是判断空白字符串

## 0.1a2

- 新增：提供 Respond 管理请求响应