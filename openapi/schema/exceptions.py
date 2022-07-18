class ValidationError(Exception):
    def __init__(self, message):
        self.message = message


class SerializationError(Exception):
    def __init__(self, message):
        self.message = message


class DeserializationError(Exception):
    def __init__(self, error):
        self.error = error

    def __str__(self):
        if isinstance(self.error, (list, tuple)) and len(self.error) == 1:
            return str(self.error[0])
        return str(self.error)
