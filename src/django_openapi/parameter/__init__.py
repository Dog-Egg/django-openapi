import typing as _t

from .parameters import Body as __B
from .parameters import Cookie as __C
from .parameters import Header as __H
from .parameters import Path
from .parameters import Query as __Q
from .style import Style

Query = _t.cast(_t.Any, __Q)
Cookie = _t.cast(_t.Any, __C)
Header = _t.cast(_t.Any, __H)
Body = _t.cast(_t.Any, __B)
