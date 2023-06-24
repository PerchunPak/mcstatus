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
from ..save_result import save_result
from .comparer import Comparer, LIST_OF_DIFFERENCES, SubDifference

console = Console()


def get_servers_to_ping() -> list[ServerForTesting]:
    with DATA_FOR_TESTING_FILE.open("r") as f:
        return json.load(f)


async def ping_server(server_to_ping: ServerForTesting) -> t.Literal[False] | LIST_OF_DIFFERENCES:
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

    differences = Comparer(server_to_ping["expected"], actual).compare()
    save_result(server_to_ping, actual, differences if differences != [] else None)
    return differences


def handle_results(tasks: set[asyncio.Task], _) -> dict[str, t.Literal[False] | LIST_OF_DIFFERENCES]:
    results: dict[str, t.Literal[False] | LIST_OF_DIFFERENCES] = {}
    for task in tasks:
        results[task.get_name()] = task.result()
    return results


async def ping_servers(servers: list[ServerForTesting]) -> dict[str, t.Literal[False] | LIST_OF_DIFFERENCES]:
    return handle_results(
        *await asyncio.wait(
            {asyncio.create_task(ping_server(server_to_ping), name=server_to_ping["id"]) for server_to_ping in servers}
        )
    )


def print_results(results: dict[str, t.Literal[False] | LIST_OF_DIFFERENCES], servers: list[ServerForTesting]) -> None:
    table = Table("ID", "Port", "Result")

    for server_id, result in results.items():
        server = next(filter(lambda x: x["id"] == server_id, servers))
        table.add_row(server_id, str(server["port"]), "[green]OK" if result == [] else "[red]FAIL")

    console.print(table)

    failed_servers = list(filter(lambda x: x[1] != [], results.items()))
    print_failed_servers(failed_servers)

    print("Total failed servers: " + str(get_count_of_failed_servers(results)))


def print_failed_servers(failed_servers: list[tuple[str, LIST_OF_DIFFERENCES]]) -> None:
    sub_differences: list[tuple[str, LIST_OF_DIFFERENCES]] = []

    for id, failed_server_differences in failed_servers:
        table = Table("Key", "Expected", "Actual", title=id, show_lines=True)
        for difference in failed_server_differences:
            if isinstance(difference, SubDifference):
                sub_differences.append((id + f".{difference.key}", difference.value))
                continue
            table.add_row(str(difference.key), str(difference.one), str(difference.two))
        console.print(table)

    if len(sub_differences) > 0:
        print_failed_servers(sub_differences)


def get_count_of_failed_servers(results: dict[str, t.Literal[False] | LIST_OF_DIFFERENCES]) -> int:
    return len(list(filter(lambda x: x != [], results.values())))


async def main() -> int:
    servers = get_servers_to_ping()
    results: dict[str, t.Literal[False] | LIST_OF_DIFFERENCES] = {}

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
