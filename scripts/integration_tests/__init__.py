"""
TODO
  - [x] Write simple script, that pings all ports and checks if the server there is online.
  - [x] Improve the script, to transform answer objects into JSON.
  - [x] Improve the script that generates data, to generate expected results data.
  - [ ] Find and print differences between expected and actual results.
  - [ ] If got an exception, write it's traceback (formatted by rich) into file and upload it as artifact.
  - [ ] Write `data.json` file for auto-generating.
  - [ ] Write docstrings.
"""
from pathlib import Path

PACKAGE_DIR = Path(__file__).parent
DATA_DIR = PACKAGE_DIR / "data"

CI_FILE = PACKAGE_DIR.parent.parent / ".github" / "workflows" / "integration-tests.yml"
DATA_FOR_GENERATING_FILE = DATA_DIR / "for_generating.json"
DATA_FOR_TESTING_FILE = DATA_DIR / "for_testing.json"
