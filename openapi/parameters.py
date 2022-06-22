from openapi.schema.properties import Property


class Parameter:
    type = None

    # noinspection PyShadowingBuiltins
    def __init__(self, property: Property, *, in_=None):
        self.property = property
        self.in_ = in_
