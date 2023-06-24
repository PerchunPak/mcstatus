import dataclasses
import json
import typing as t

from . import SAVING_DIR
from .models import ServerForTesting
from .testing.comparer import LIST_OF_DIFFERENCES


def save_result(from_config: ServerForTesting, actual: dict[str, t.Any], differences: LIST_OF_DIFFERENCES | None) -> None:
    folder_to_save = SAVING_DIR / from_config["id"]
    folder_to_save.mkdir(exist_ok=True)
    for file_name, data in [("actual", actual), ("from_config", from_config)] + (
        [] if differences is None else [("differences", list(map(dataclasses.asdict, differences)))]
    ):
        with (folder_to_save / f"{file_name}.json").open("w") as f:
            json.dump(data, f, indent=4)
