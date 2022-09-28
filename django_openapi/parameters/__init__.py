import typing as _t

from .parameters import (
    Query as _Query,
    Cookie as _Cookie,
    Header as _Header,
    Body as _Body,
)
from .style import Style

Query = _t.cast(_t.Any, _Query)
Cookie = _t.cast(_t.Any, _Cookie)
Header = _t.cast(_t.Any, _Header)
Body = _t.cast(_t.Any, _Body)
