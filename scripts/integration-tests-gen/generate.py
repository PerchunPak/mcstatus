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

import configparser
import hashlib
import sys
import json
from collections import defaultdict
from glob import glob
from pathlib import Path
import typing as t

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

def parse_minecraft_core(data: MinecraftCoreData) -> str:
    parsed = ""
    if "versions" in data:
        assert len(data["versions"]) > 0 and data["image"] == "itzg/minecraft-server"
    else:
        data["versions"] = [None]
        
    for version in data["versions"]:
        parsed += f"{id}:\n"
        parsed += f"    image: {data['image']}\n"

        if version:
            data.setdefault("env", {})
            data["env"]["VERSION"] = version
        
        if data["image"] == "itzg/minecraft-server":
            data.setdefault("env", {})
            data["env"]["EULA"] = "TRUE"

        if "env" in data:
            parsed += f"    env:\n"
            for key, value in data["env"].items():
                parsed += f"      {key}: {value}\n"

        parsed += f"    options: >-"
        parsed += f"\n              ".join(data["args"])
        parsed += "\n\n\n"
    return parsed


def write_yaml_file(services: str) -> None:
    with open(CI_FILE, "r") as f:
        ci_file = f.read()
    



def get_yaml_files_hash():
    """Calculate a hash of all the yaml configuration files"""

    hasher = hashlib.md5()
    path_pattern = (OUT_DIR / "test-integration-*.yml").as_posix()
    for file in glob(path_pattern):
        with open(file, "rb") as f:
            buf = f.read()
            hasher.update(buf)

    return hasher.hexdigest()


def main(fail_on_changes: bool) -> None:
    if fail_on_changes:
        old_hash = get_yaml_files_hash()

    print("Reading data for generating")
    with open(DATA_FOR_GENERATING, "r") as data_file:
        data: list[MinecraftCoreData] = json.load(data_file)

    output = ""
    for minecraft_core in data:
        output += SERVICE_TEMPLATE.format(**minecraft_core)

    write_yaml_file(output)

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
    fail_on_changes = (
        True if len(sys.argv) == 2 and sys.argv[1] == "--fail-on-changes" else False
    )
    main(fail_on_changes)
