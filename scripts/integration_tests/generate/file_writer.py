import json

from .. import CI_FILE, DATA_FOR_TESTING_FILE
from ..models import ServerForTesting


class FileWriter:
    def __init__(self, new_text: str, servers_for_testing: list[ServerForTesting]) -> None:
        self.new_text = new_text
        self.servers_for_testing = servers_for_testing

    def write(self) -> None:
        self.new_text = self._add_tabs_to_generated_data()
        to_replace = self._get_text_to_replace()
        self._write_the_result(to_replace)
        self._write_for_testing_data()

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

    def _write_for_testing_data(self) -> None:
        with DATA_FOR_TESTING_FILE.open("w") as f:
            json.dump(self.servers_for_testing, f, indent=2)
