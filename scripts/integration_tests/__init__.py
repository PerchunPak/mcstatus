"""
TODO
  - [x] Write simple script, that pings all ports and checks if the server there is online.
  - [x] Improve the script, to transform answer objects into JSON.
  - [x] Improve the script that generates data, to generate expected results data.
  - [x] Find and print differences between expected and actual results.
  - [x] If got an exception, write it's traceback (formatted by rich) into file and upload it as artifact.
  - [ ] Support Bedrock and Query.
  - [ ] Write docstrings.
  - [ ] Write `data.json` file for auto-generating.
"""
from pathlib import Path

PACKAGE_DIR = Path(__file__).parent
ROOT_DIR = PACKAGE_DIR.parent.parent
DATA_DIR = PACKAGE_DIR / "data"
SAVING_DIR = ROOT_DIR / "results"
SAVING_DIR.mkdir(exist_ok=True)

CI_FILE = ROOT_DIR / ".github" / "workflows" / "integration-tests.yml"
DATA_FOR_GENERATING_FILE = DATA_DIR / "for_generating.json"
DATA_FOR_TESTING_FILE = DATA_DIR / "for_testing.json"
