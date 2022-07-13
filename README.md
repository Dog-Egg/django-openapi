# Django-OpenAPI (开发中...)

通过接口定义，实现文档生成、参数校验、响应数据序列化、API接口自动测试...

[文档地址](https://dog-egg.github.io/django-openapi/)

![demo](./screenshots/1.png)

## 待办清单

### 基础

- [x] 基础结构
- [x] 路由注册
- [x] Request Body Content-Type
- [ ] 表述 authentication specification (401, 403)
- [ ] 代理处理

### Schema

- [x] API结构
- [x] Schema 字段嵌套
- [x] Schema 字段继承
- [ ] 各种类型字段序列反序列实现
    - [x] List
    - [x] String
    - [x] Integer
    - [x] Float
    - [ ] Decimal
    - [ ] Datetime
    - [ ] Time
    - [ ] Date
    - [ ] Url
    - [x] Boolean
    - [ ] Email
    - [x] File
- [ ] 自定义字段
- [ ] 各类验证器
    - [x] [Numeric Instances](https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-num)
    - [x] [Strings](https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-str)
    - [ ] [Arrays](https://json-schema.org/draft/2020-12/json-schema-validation.html#name-validation-keywords-for-arr)

### Specification

- [x] Components Object 自动注册、引用
- [ ] _schema to specification_ (自定义字段？)

### 配置

- [ ] Response Schema (200, 400, 500...)

### 扩展

- [ ] QuerySet 分页
- [ ] Django Model to Schema