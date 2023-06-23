import asyncio
import typing as t

import typer
import typing_extensions as te

from .generate import main as generate_logic
from .testing import main as testing_logic

app = typer.Typer()


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
