import typing as t

import typing_extensions as te


class ServerForTesting(te.TypedDict):
    id: str
    port: int
    expected: dict[str, t.Any] | dict[str, dict[str, t.Any]]
