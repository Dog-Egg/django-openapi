import typing
from collections.abc import Mapping
from operator import getitem


class Style:
    # MATRIX = 'matrix'
    # LABEL = 'label'
    # DEEP_OBJECT = 'deepObject'
    FORM = 'form'
    SIMPLE = 'simple'
    SPACE_DELIMITED = 'spaceDelimited'
    PIPE_DELIMITED = 'pipeDelimited'

    def __init__(
            self,
            style: str = None,
            explode: bool = None,
    ):
        self._style = style
        self._explode = explode
        self._schema = None

    @property
    def type(self):
        # noinspection PyProtectedMember
        data_type = self.schema._metadata['data_type']
        if data_type in ('array', 'object'):
            return data_type
        return 'primitive'

    @property
    def schema(self):
        return self._schema  # type: ignore

    @schema.setter
    def schema(self, value):
        assert self._schema is None
        self._schema = value

    def get_style_and_explode(self, location: str) -> typing.Tuple[str, bool]:
        style = {
            'query': self.FORM,
            'path': self.SIMPLE,
            'header': self.SIMPLE,
            'cookie': self.FORM,
        }[location] if self._style is None else self._style
        explode = style == self.FORM if self._explode is None else self._explode
        return style, explode


def getlist(data, key):
    return data.getlist(key)


def comma_split(*args):
    value: str = getitem(*args)
    return value.split(',')


def pipe_split(*args):
    value: str = getitem(*args)
    return value.split('|')


def space_split(*args):
    value: str = getitem(*args)
    return value.split(' ')


class StyleParser:
    GETTERS = {
        (Style.FORM, True, 'array', 'query'): getlist,
        (Style.FORM, False, 'array', 'query'): comma_split,
        (Style.FORM, True, 'primitive', 'query'): getitem,
        (Style.FORM, True, 'primitive', 'cookie'): getitem,
        (Style.SIMPLE, False, 'primitive', 'header'): getitem,
        (Style.SIMPLE, False, 'primitive', 'path'): getitem,
        (Style.SIMPLE, False, 'array', 'path'): comma_split,
        (Style.PIPE_DELIMITED, False, 'array', 'query'): pipe_split,
        (Style.SPACE_DELIMITED, False, 'array', 'query'): space_split,
    }

    def __init__(self, styles: typing.Dict[str, Style], location):
        self.key_to_getter = {}
        for key, s in styles.items():
            style, explode = s.get_style_and_explode(location)
            try:
                getter = self.GETTERS[(style, explode, s.type, location)]
            except KeyError:
                raise TypeError('Not support <style: %r, explode: %s, type: %r> in %r.' % (
                    style, explode, s.type, location))
            self.key_to_getter[key] = getter

    def parse(self, data) -> dict:
        assert isinstance(data, Mapping), data
        copy_data = dict(data)
        for key, getter in self.key_to_getter.items():
            if key in data:
                copy_data[key] = getter(data, key)  # type: ignore
        return copy_data
