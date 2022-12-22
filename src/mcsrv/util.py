import os
import pathlib
import re

import click
from click import echo
from colorama import Fore


class Screen:
    def __init__(self, sock: str):
        s = sock.split(".", 1)
        self.pid: int = int(s[0])
        self.name: str = s[1]

    def __repr__(self):
        return f"{self.pid}.{self.name}"

    def __str__(self):
        return self.__repr__()


def get_running_screens() -> list[Screen]:
    screen_dir = pathlib.Path(f"/run/screen/S-{os.getlogin()}")

    if not screen_dir.is_dir():
        return []

    return [Screen(s.name) for s in screen_dir.glob("*.mc-*")]


XMX_GM = re.compile(r"[0-9]+G|M")
XMX_G = re.compile(r"[0-9]+")


def check_ram_argument(i: str) -> str:
    if XMX_GM.match(i):
        return i

    if XMX_G.match(i):
        return f"{i}G"

    echo(f"mcsrv: {Fore.RED}Invalid RAM value: {i}")
    raise click.exceptions.Exit(code=1)


def clean_path(p: pathlib.Path) -> pathlib.Path:
    out = []

    for part in p.parts:
        if part == "..":
            out.pop()
            continue

        if part == ".":
            continue

        out.append(part)

    return pathlib.Path("/").joinpath(*out)


printed_warnings = []


def print_warning(s: str, id_: str):
    if id_ not in printed_warnings:
        click.echo(s)
        printed_warnings.append(id_)
