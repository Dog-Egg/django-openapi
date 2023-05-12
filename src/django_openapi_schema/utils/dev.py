import typing as t


def join(items: t.Sequence[str]):
    """
    >>> join(['A'])
    'A'

    >>> join(['A', 'B'])
    "'A' or 'B'"

    >>> join(['A', 'B', 'C'])
    "'A', 'B' or 'C'"
    """
    if len(items) == 1:
        return items[0]
    return f'{", ".join(repr(i) for i in  items[:-1])} or {items[-1]!r}'
