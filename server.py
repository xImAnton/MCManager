import os
import pathlib
import re
import shlex
import subprocess
from functools import cached_property
from typing import Optional

import click.exceptions
import inquirer
from click import echo

from screen import get_running_servers, Screen

RC_PATH = pathlib.Path("~/.mcsrvrc")


def check_ram_argument(i: str) -> str:
    if re.match(r"[0-9]+G|M", i):
        return f"-Xmx{i}"

    if re.match(r"[0-9]+", i):
        return f"-Xmx{i}G"

    raise click.exceptions.Exit(code=1)


class ServerInformation:
    @classmethod
    def from_cwd(cls):
        return ServerInformation(os.getcwd())

    @classmethod
    def get_registered_servers(cls) -> list[str]:
        if not RC_PATH.is_file():
            return []

        with RC_PATH.open("r") as f:
            return f.readlines()

    def __init__(self, path: str):
        self.path: pathlib.Path = pathlib.Path(path).absolute()
        self.data: dict[str, str] = {}
        self._load_data()
        self.jar: pathlib.Path = self._locate_jar()
        self.save_data()
        self.register()

    def register(self) -> None:
        if str(self.path) in self.get_registered_servers():
            return

        with RC_PATH.open("a" if RC_PATH.is_file() else "w") as f:
            f.write(f"{self.path}\n")

    @property
    def running(self) -> bool:
        return self.screen_handle is not None

    @cached_property
    def screen_handle(self) -> Optional[Screen]:
        for screen in get_running_servers():
            if screen.name == self.screen_name:
                return screen
        return None

    @property
    def id(self) -> str:
        return self.path.name

    @property
    def datafile(self) -> pathlib.Path:
        return self.path.joinpath(".mcsrvmeta")

    @property
    def screen_name(self):
        return f"mc-{self.id}"

    def send_command(self, cmd: str, execute: bool = True) -> None:
        if execute:
            cmd += "^M"

        subprocess.run(["screen", "-S", self.screen_name, "-p", "0", "-X", "stuff", cmd])

    def start(self, ram: str = None) -> None:
        ram = check_ram_argument(ram if ram else self.data.get("ram", "4G"))

        echo(f"starting server {self.id} with ram {ram}")
        subprocess.run(["screen", "-d", "-S", self.screen_name, "-m", "java", ram, "-jar", self.jar.name])

    def _locate_jar(self) -> pathlib.Path:
        if "jar" in self.data:
            j = self.path.joinpath(self.data["jar"])
            if j.is_file():
                return j

        jars = list(self.path.glob("*.jar"))

        if len(jars) == 0:
            echo("no server found in the current directory")
            raise click.exceptions.Exit(code=1)

        if len(jars) == 1:
            self.data["jar"] = jars[0].name
            return jars[0]

        answer = inquirer.prompt([inquirer.List("jar", message="Which .jar runs your server?", choices=jars)])

        if not answer:
            raise click.exceptions.Exit(code=1)

        self.data["jar"] = answer["jar"].name
        return answer["jar"]

    def open_console(self):
        os.system(shlex.join(["screen", "-x", str(self.screen_handle)]))

    def save_data(self):
        with self.datafile.open("w") as f:
            for key, val in self.data.items():
                f.write(f"{key}={val}\n")

    def _load_data(self) -> None:
        self.data = {}

        if not self.datafile.is_file():
            return

        with self.datafile.open("r") as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("#"):
                    continue

                res = line.split("=", 1)

                if len(res) != 2:
                    continue

                self.data[res[0]] = res[1]
