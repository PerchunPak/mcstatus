import hashlib
import json
import typing as t

from .. import CI_FILE, DATA_FOR_GENERATING_FILE, DATA_FOR_TESTING_FILE
from ..models import ServerForTesting
from .file_writer import FileWriter
from .models import MinecraftCoreData
from .service_info import ServiceInfo


def get_hash() -> str:
    """Hash all generated files and return the hash."""
    hasher = hashlib.sha256()
    hasher.update(CI_FILE.read_bytes())
    hasher.update(DATA_FOR_GENERATING_FILE.read_bytes())
    hasher.update(DATA_FOR_TESTING_FILE.read_bytes())
    return hasher.hexdigest()


def get_data() -> list[MinecraftCoreData]:
    with DATA_FOR_GENERATING_FILE.open("r") as data_file:
        return t.cast("list[MinecraftCoreData]", json.load(data_file))


def parse_data(data: list[MinecraftCoreData]) -> tuple[str, list[ServerForTesting]]:
    output = ""
    for_testing: list[ServerForTesting] = []
    for minecraft_core in data:
        as_objects = ServiceInfo.from_dict(minecraft_core)
        for service in as_objects:
            port = 25565 + len(for_testing)
            for_testing.append(
                {
                    "id": service.id,
                    "port": port,
                    "expected": service.expected,
                }
            )
            service.attach_port(port)
            output += service.to_yaml() + "\n"
    if output.endswith("\n"):
        output = output[:-1]

    return output, for_testing


def main(fail_on_changes: bool) -> None:
    if fail_on_changes:
        old_hash = get_hash()

    data = get_data()
    output, for_testing = parse_data(data)

    FileWriter(output, for_testing).write()

    if fail_on_changes:
        new_hash = get_hash()

        if old_hash != new_hash:
            raise RuntimeError(  # todo update this message
                "The yaml configuration files have changed. This means that tox.ini has changed "
                "but the changes have not been propagated to the GitHub actions config files. "
                "Please run `python scripts/split-tox-gh-actions/split-tox-gh-actions.py` "
                "locally and commit the changes of the yaml configuration files to continue. "
            )

    print("All done. Have a nice day!")
