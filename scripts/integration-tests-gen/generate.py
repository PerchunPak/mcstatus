"""Generate Integration Tests CI.

As we have many cores to test, we want to be it in parallel and automatically generated.
We parallel them with matrix strategy in GitHub Actions and automatically generate this matrix
here.

This is a small script to split a tox.ini config file into multiple GitHub actions configuration files.
This way each framework defined in tox.ini will get its own GitHub actions configuration file
which allows them to be run in parallel in GitHub actions.

This will generate/update several configuration files, that need to be commited to Git afterwards.
Whenever tox.ini is changed, this script needs to be run.

Usage:
    python split-tox-gh-actions.py [--fail-on-changes]

If the parameter `--fail-on-changes` is set, the script will raise a RuntimeError in case the yaml
files have been changed by the scripts execution. This is used in CI to check if the yaml files
represent the current tox.ini file. (And if not the CI run fails.)






TODO
  - [ ] Write template for generating.
  - [ ] Find what strings we need to replace.
  - [ ] Replace strings.
  - [ ] Write `data.json` file for autogenerating.
"""
from __future__ import annotations

import configparser
import hashlib
import sys
import json
from collections import defaultdict
from glob import glob
from pathlib import Path
import typing as t
import dataclasses

if t.TYPE_CHECKING:
    import typing_extensions as te

    class MinecraftCoreData(t.TypedDict):
        id: str
        image: str
        versions: te.NotRequired[list[str]]
        env: te.NotRequired[dict[str, str]]
        options: te.NotRequired[list[str]]

else:
    MinecraftCoreData = {}

CI_FILE = Path(__file__).resolve().parent.parent.parent / ".github" / "workflows" / "integration-tests.yml"
TEMPLATE_DIR = Path(__file__).resolve().parent
DATA_FOR_GENERATING = TEMPLATE_DIR / "data.json"
TEMPLATE_FILE = TEMPLATE_DIR / "ci-yaml.txt"
TEMPLATE_FILE_SERVICES = TEMPLATE_DIR / "ci-yaml-services.txt"


@dataclasses.dataclass
class ServiceInfo:
    id: str
    image: str
    env: dict[str, str] | None
    options: list[str] | None

    @classmethod
    def from_dict(cls, data: MinecraftCoreData) -> list[te.Self]:
        output: list[ServiceInfo] = []
        if "versions" in data:
            assert len(data["versions"]) > 0 and data["image"] == "itzg/minecraft-server"
        else:
            data["versions"] = [None]

        for version in data["versions"]:
            id = data["id"] + (f"-{version}" if version else "")

            if version:
                data.setdefault("env", {})
                data["env"]["VERSION"] = version

            if data["image"] == "itzg/minecraft-server":
                data.setdefault("env", {})
                data["env"]["EULA"] = "TRUE"

            output.append(
                cls(
                    id=id,
                    image=data["image"],
                    env=data.get("env"),
                    options=data.get("options"),
                )
            )

        return output

    def attach_port(self, port: int) -> None:
        if self.image == "itzg/minecraft-server":
            self.env = {} if self.env is None else self.env
            self.env["SERVER_PORT"] = str(port)
        else:
            assert self.env is not None
            for key, value in self.env.items():
                self.env[key] = value.replace("{{ PORT }}", str(port))

    def to_yaml(self) -> str:
        output = f"{self.id}:\n"
        output += f"  image: {self.image}\n"

        if self.env:
            output += "  env:\n"
            for key, value in self.env.items():
                output += f"    {key}: {value}\n"

        if self.options:
            output += "  options: >-\n            "
            output += "\n            ".join(self.options) + "\n"

        return output


class FileWriter:
    def __init__(self, new_text: str) -> None:
        self.new_text = new_text

    def write(self) -> None:
        self.new_text = self._add_tabs_to_generated_data()
        to_replace = self._get_text_to_replace()
        self._write_the_result(to_replace)

    def _add_tabs_to_generated_data(self, tabs_count: int = 3) -> str:
        output = ""
        for line in self.new_text.split("\n"):
            output += "  " * tabs_count + line + "\n"
        return output

    def _get_text_to_replace(self) -> str:
        old_text = ""
        active = False
        with CI_FILE.open("r") as f:
            for line in f.readlines():
                if line == "    services:\n":
                    assert not active, "Two times declared services?"
                    active = True
                elif line == "    steps:\n":
                    break
                elif active:
                    old_text += line
        return old_text

    def _write_the_result(self, old_text: str) -> None:
        with CI_FILE.open("r") as f:
            entire_text = f.read()
        with CI_FILE.open("w") as f:
            f.write(entire_text.replace(old_text, self.new_text))


def get_yaml_files_hash():
    """Calculate a hash of all the yaml configuration files"""

    hasher = hashlib.md5()
    with open(CI_FILE, "rb") as f:
        buf = f.read()
        hasher.update(buf)

    return hasher.hexdigest()


def main(fail_on_changes: bool) -> None:
    if fail_on_changes:
        old_hash = get_yaml_files_hash()

    print("Reading data for generating")
    with DATA_FOR_GENERATING.open("r") as data_file:
        data: list[MinecraftCoreData] = json.load(data_file)

    output = ""
    ports = []
    for minecraft_core in data:
        as_objects = ServiceInfo.from_dict(minecraft_core)
        for service in as_objects:
            ports.append(port := 25565 + len(ports))
            service.attach_port(port)
            output += service.to_yaml() + "\n"

    FileWriter(output).write()

    if fail_on_changes:
        new_hash = get_yaml_files_hash()

        if old_hash != new_hash:
            raise RuntimeError(
                "The yaml configuration files have changed. This means that tox.ini has changed "
                "but the changes have not been propagated to the GitHub actions config files. "
                "Please run `python scripts/split-tox-gh-actions/split-tox-gh-actions.py` "
                "locally and commit the changes of the yaml configuration files to continue. "
            )

    print("All done. Have a nice day!")


if __name__ == "__main__":
    main(fail_on_changes=True if len(sys.argv) == 2 and sys.argv[1] == "--fail-on-changes" else False)
