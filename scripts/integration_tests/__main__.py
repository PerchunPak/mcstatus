import asyncio
import typing as t

import typer
import typing_extensions as te

from .generate import main as generate_logic
from .testing import main as testing_logic

app = typer.Typer(help="""
This is a script, that we use for integration testing.

You need to write data for generating into 'data/for_generating.json' file.
Do not touch the other file, 'data/for_testing.json', it needs to be generated via
'python -m scripts.integration_tests generate' command.
""")


@app.command()
def generate(
    fail_on_changes: te.Annotated[bool, typer.Option(help="Fail if there were generated any changes.")] = False
) -> None:
    """Generate configuration in CI file and data for testing."""
    generate_logic(fail_on_changes)


@app.command()
def test() -> None:
    """Run all integration tests based on generated data."""
    exit_code = asyncio.run(testing_logic())
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()
