import contextlib
import typing as t
from collections import ChainMap
from contextvars import ContextVar

from ._error_messages import DEFAULT_ERROR_MESSAGES

error_message_cv = ContextVar("error_messages")


@contextlib.contextmanager
def error_message_context(error_messages: dict):
    token = error_message_cv.set(error_messages)
    try:
        yield
    finally:
        error_message_cv.reset(token)


class MessageBuilder:
    def __init__(self, message=None, key=None) -> None:
        assert message is not None or key is not None
        self.message = message
        self.key = key

    def build_message(self, error_messages: t.Mapping):
        if self.message:
            return self.message
        return error_messages[self.key]


class ValidationError(Exception):
    def __init__(self, message: t.Any = None, key=None):
        if message is not None or key is not None:
            message_builders = [MessageBuilder(message, key)]
        else:
            message_builders = []
        self.__message_builders: t.List[MessageBuilder] = message_builders

        self.__item_errors: t.Dict[t.Union[int, str], ValidationError] = {}
        self.__local_error_messages = {}

    def __build_messages(self):
        context_error_messages = error_message_cv.get({})
        error_messages = ChainMap(
            self.__local_error_messages,
            context_error_messages,
            DEFAULT_ERROR_MESSAGES,
        )
        return [m.build_message(error_messages) for m in self.__message_builders]

    def concat_error(self, error: "ValidationError"):
        self.__message_builders.extend(error.__message_builders)

    def setitem_error(self, key: t.Union[str, int], error: "ValidationError"):
        assert key not in self.__item_errors
        self.__item_errors[key] = error

    def update_error_message(self, error_messages: dict):
        self.__local_error_messages.update(error_messages)

    @property
    def _nonempty(self) -> bool:
        return bool(self.__item_errors or self.__message_builders)

    def __str__(self):
        return str(self.format_errors())

    def format_errors(self) -> list:
        results = []
        if self.__message_builders:
            results.append(dict(msgs=self.__build_messages()))

        if self.__item_errors:
            items = []

            def recursion(err: ValidationError, path: list):
                for k, e in err.__item_errors.items():
                    p = path[:]
                    p.append(k)
                    if e.__message_builders:
                        items.append(
                            {
                                "msgs": e.__build_messages(),
                                "loc": p,
                            }
                        )
                    if err.__item_errors:
                        recursion(e, p)

            recursion(self, [])
            results.extend(items)

        return results
