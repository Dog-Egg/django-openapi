import typing
from collections import defaultdict

from openapi.schemax.validators import Validator
from openapi.schemax.exceptions import ValidationError
from openapi.schemax.utils import PureObject, make_instance

undefined = object()


class _Field:
    def __init__(
            self,
            *,
            name: str = None,
            required: bool = False,
            default=undefined,
            default_factory: typing.Callable[[], typing.Any] = None,
            validators: typing.List[Validator] = None
    ):
        if default is not undefined and default_factory is not None:
            raise ValueError('不能同时定义 default 和 default_factory')

        self.name = name
        self.attr = None
        self.required = required
        self.default = default
        self.default_factory = default_factory
        self.validators = validators or []

    def deserialize(self, value):
        value = self._deserialize(value)
        errors = []

        for validator in self.validators:
            try:
                validator.validate(value)
            except ValidationError as exc:
                errors.append(exc.message)

        if errors:
            raise ValidationError(errors)
        return value

    def _deserialize(self, value):
        raise NotImplementedError


class _ContainerFieldFlag:
    pass


class Schema(_Field, _ContainerFieldFlag):
    _fields: typing.List[_Field]

    def __init_subclass__(cls):
        cls._fields = []
        for name, field in vars(cls).items():
            if isinstance(field, _Field):
                field.attr = name
                if field.name is None:
                    field.name = name
                cls._fields.append(field)

    def _deserialize(self, value):
        kwargs = {}
        errors = defaultdict(list)

        for field in self._fields:
            if field.name not in value:
                # required
                if field.required:
                    errors[field.name].append('这个字段是必需的')

                # default
                if field.default is not undefined:
                    kwargs[field.attr] = field.default
                elif field.default_factory is not None:
                    kwargs[field.attr] = field.default_factory()

                continue

            try:
                kwargs[field.attr] = field.deserialize(value[field.name])
            except ValidationError as exc:
                field_name = field.name
                if isinstance(field, _ContainerFieldFlag):
                    errors[field_name] = exc.message
                else:
                    if isinstance(exc.message, list):
                        errors[field_name].extend(exc.message)
                    else:
                        errors[field_name].append(exc.message)

        if errors:
            raise ValidationError(dict(errors))
        return PureObject(**kwargs)


class String(_Field):
    def __init__(self, *args, strip=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.strip = strip

    def _deserialize(self, value):
        string = str(value)
        if self.strip:
            string = string.strip()
        return string


class Integer(_Field):
    def _deserialize(self, value):
        try:
            return int(value)
        except ValueError:
            raise ValidationError('不是一个整数')


class List(_Field, _ContainerFieldFlag):
    def __init__(self, field_or_cls: typing.Union[_Field, typing.Type[_Field]], *args, **kwargs):
        self._field: _Field = make_instance(field_or_cls)
        super().__init__(*args, **kwargs)

    def _deserialize(self, value):
        rv = []
        errors = defaultdict(list)

        for index, item in enumerate(value):
            try:
                rv.append(self._field.deserialize(item))
            except ValidationError as exc:
                errors[index].append(exc.message)

        if errors:
            raise ValidationError(dict(errors))
        return rv


class Any(_Field):
    def _deserialize(self, value):
        return value
