import os
import pathlib
import re
import subprocess

import click.exceptions
import inquirer

from click import echo

from screen import get_running_servers


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

    def __init__(self, path: str):
        self.path: pathlib.Path = pathlib.Path(path)
        self.data: dict[str, str] = {}
        self._load_data()
        self.jar: pathlib.Path = self._locate_jar()
        self.save_data()

    def send_command(self, cmd: str) -> None:
        subprocess.run(["screen", "-S", self.screen_name, "-p", "0", "-X", "stuff", cmd + "^M"])

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

    @property
    def running(self) -> bool:
        return self.id in get_running_servers()

    @property
    def id(self) -> str:
        return self.path.name

    @property
    def datafile(self) -> pathlib.Path:
        return self.path.joinpath(".mcsrvmeta")

    @property
    def screen_name(self):
        return f"mc-{self.id}"

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
