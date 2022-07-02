class SerializationError(Exception):
    pass


class DeserializationError(Exception):
    def __init__(self, message=None):
        self.message = message
