import inspect


def default_as_none(value, default):
    if value is default:
        return None
    return value


def clean_commonmark(text: str):
    if not text:
        return None
    return inspect.cleandoc(text)
