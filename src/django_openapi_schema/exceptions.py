import typing as t


class ValidationError(Exception):
    def __init__(self, message: t.Any = None):
        self.__messages = [] if message is None else [message]
        self.__item_errors: t.Dict[t.Union[int, str], ValidationError] = {}

    def _concat_error(self, error: "ValidationError"):
        assert not self.__item_errors
        self.__messages.extend(error.__messages)

    def _setitem_error(self, key: t.Union[str, int], error: "ValidationError"):
        assert not self.__messages
        assert key not in self.__item_errors
        self.__item_errors[key] = error

    @property
    def _nonempty(self) -> bool:
        return bool(self.__item_errors or self.__messages)

    def __str__(self):
        return str(self.format_errors())

    def format_errors(self) -> list:
        results = []
        if self.__messages:
            results.append(dict(msgs=self.__messages))

        if self.__item_errors:
            r = []

            def recursion(err: ValidationError, path: list):
                for k, e in err.__item_errors.items():
                    p = path[:]
                    p.append(k)
                    if e.__messages:
                        r.append(
                            {
                                "msgs": e.__messages,
                                "loc": p,
                            }
                        )
                    if err.__item_errors:
                        recursion(e, p)

            recursion(self, [])
            results.extend(r)

        return results
