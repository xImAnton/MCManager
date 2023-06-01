import pathlib
from typing import Optional

import click
import inquirer
from colorama import Fore

from .launch import LaunchMethod


class JarLaunchMethod(LaunchMethod):
    METHOD = "jar"

    @classmethod
    def could_satisfy(cls, path: pathlib.Path) -> Optional[str]:
        jars = list(path.glob("*.jar"))

        if not jars:
            return

        choices = list(map(lambda x: (x.name, x.relative_to(path)), jars))
        choices.append(("Other server type...", None))

        answer = inquirer.prompt([inquirer.List("jar", message="Which .jar runs your server?", choices=choices)])

        if not answer:
            raise click.exceptions.Exit(code=1)

        return answer["jar"]  # None if other type, else jar location

    def get_command(self, java: str, ram: str):
        return [java, "-Xmx" + ram, "-jar", self.args]

    def is_valid(self):
        j = self.path.joinpath(self.args)

        if not j.is_file():
            click.echo(f"{Fore.YELLOW}Earlier used Jar-File not found! Locating...")
            return False

        return True
