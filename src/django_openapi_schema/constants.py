#: 空
EMPTY = type(
    "EMPTY",
    (),
    dict(
        __bool__=lambda _: False,
        __repr__=lambda _: "EMPTY",
    ),
)()
