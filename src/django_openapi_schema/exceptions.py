import typing as t


class ValidationError(Exception):
    def __init__(self, message: t.Any = None):
        self._messages = [] if message is None else [message]
        self._field_errs: t.Dict[t.Union[int, str], ValidationError] = {}

    def concat_error(self, error: "ValidationError"):
        assert not self._field_errs
        self._messages.extend(error._messages)

    def set_field_error(self, key: t.Union[str, int], error: "ValidationError"):
        assert not self._messages
        assert key not in self._field_errs
        self._field_errs[key] = error

    @property
    def nonempty(self) -> bool:
        return bool(self._field_errs or self._messages)

    def __str__(self):
        return str(self.format_errors())

    def format_errors(self) -> dict:
        results = {}
        if self._messages:
            results.update(msgs=self._messages)

        if self._field_errs:
            fields = []

            def recursion(err: ValidationError, path: list):
                for k, e in err._field_errs.items():
                    _path = path[:]
                    _path.append(k)
                    if e._messages:
                        fields.append(
                            {
                                "loc": _path,
                                "msgs": e._messages,
                            }
                        )
                    if err._field_errs:
                        recursion(e, _path)

            recursion(self, [])
            results.update(fields=fields)

        return results
