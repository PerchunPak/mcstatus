import typing as t

import typing_extensions as te


class MinecraftCoreData(te.TypedDict):
    id: str
    image: str
    versions: te.NotRequired[list[str]]
    env: te.NotRequired[dict[str, str]]
    options: te.NotRequired[list[str]]
    expected: dict[str, t.Any] | dict[str, dict[str, t.Any]]
