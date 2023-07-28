#: 空
EMPTY = type(
    "EMPTY",
    (),
    dict(
        __repr__=lambda _: "EMPTY",
    ),
)()
