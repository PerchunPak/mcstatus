from __future__ import annotations

import asyncio
import dataclasses
import json
import typing as t

import rich
from rich.console import Console
from rich.table import Table

import mcstatus

from .. import CI_FILE, DATA_FOR_GENERATING_FILE, DATA_FOR_TESTING_FILE, PACKAGE_DIR
from ..models import ServerForTesting
from .comparer import Comparer, Difference

console = Console()


def get_servers_to_ping() -> list[ServerForTesting]:
    with DATA_FOR_TESTING_FILE.open("r") as f:
        return json.load(f)


async def ping_port(port: int, expected: dict[str, t.Any]) -> t.Literal[False] | list[Difference]:
    ip = "hypixel.net"  # todo actually ping port
    try:
        status = await (await mcstatus.JavaServer.async_lookup(ip)).async_status()
    except Exception:
        return False
    actual = dataclasses.asdict(status)
    actual["motd"] = status.motd.simplify().to_minecraft()
    for unwanted_field in {"icon", "latency"}:
        del actual[unwanted_field]
    del actual["raw"]["favicon"]

    return Comparer(expected, actual).compare()


def handle_results(tasks: set[asyncio.Task], _) -> dict[str, t.Literal[False] | list[Difference]]:
    results: dict[str, t.Literal[False] | list[Difference]] = {}
    for task in tasks:
        results[task.get_name()] = task.result()
    return results


async def ping_servers(servers: list[ServerForTesting]) -> dict[str, t.Literal[False] | list[Difference]]:
    return handle_results(
        *await asyncio.wait(
            {
                asyncio.create_task(ping_port(server_to_ping["port"], server_to_ping["expected"]), name=server_to_ping["id"])
                for server_to_ping in servers
            }
        )
    )


def print_results(results: dict[str, t.Literal[False] | list[Difference]], servers: list[ServerForTesting]) -> None:
    table = Table(box=None, show_footer=True)
    table.add_column("ID")
    table.add_column("Port")
    table.add_column("Result")

    for server_id, result in results.items():
        server = next(filter(lambda x: x["id"] == server_id, servers))
        table.add_row(server_id, str(server["port"]), "[green]OK" if result == [] else "[red]FAIL")
    console.print(table)
    print("Total failed servers: " + str(get_count_of_failed_servers(results)))
    rich.print(list(results.values()))


def get_count_of_failed_servers(results: dict[str, t.Literal[False] | list[Difference]]) -> int:
    return len(list(filter(lambda x: x != [], results.values())))


async def main() -> int:
    servers = get_servers_to_ping()
    results: dict[str, t.Literal[False] | list[Difference]] = {}

    to_process: list[ServerForTesting] = []
    for server in servers:
        if len(to_process) <= 10:  # 10 means here how many servers will be pinged at once
            to_process.append(server)
            continue

        results.update(await ping_servers(to_process))
        to_process = []

    if len(to_process) > 0:
        results.update(await ping_servers(to_process))

    results = dict(sorted(results.items(), key=lambda x: next(filter(lambda e: x[0] == e["id"], servers))["port"]))

    print_results(results, servers)

    return get_count_of_failed_servers(results)
