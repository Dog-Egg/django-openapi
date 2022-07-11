from ._parameters import (
    Query as _Query,
    Cookie as _Cookie,
    Header as _Header,
    Body as _Body,
    Path as _Path
)


def _fuzzy_type(o):
    return o


Query = _fuzzy_type(_Query)
Cookie = _fuzzy_type(_Cookie)
Header = _fuzzy_type(_Header)
Body = _fuzzy_type(_Body)
Path = _fuzzy_type(_Path)
