import typing


class ValidationError(Exception):
    def __init__(self, message: str = None):
        assert message is None or isinstance(message, str)

        self._messages = [] if message is None else [message]
        self._errors: typing.Dict[
            typing.Union[int, str],
            ValidationError
        ] = {}

    def concat(self, error: 'ValidationError'):
        self._messages.extend(error._messages)

    def setitem(self, key, error: 'ValidationError'):
        assert key not in self._errors
        self._errors[key] = error

    @property
    def nonempty(self):
        return bool(self._errors or self._messages)

    def __str__(self):
        errors = self.format_errors()
        if isinstance(errors, list) and len(errors) == 1:
            return str(errors[0])
        return str(errors)

    def format_errors(self) -> typing.Union[dict, list]:
        if self._messages:
            return self._messages

        errors = {}
        for key, err in self._errors.items():
            errors[key] = err.format_errors()
        return errors
