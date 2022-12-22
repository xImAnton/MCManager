import os.path
import pathlib
import shlex
import shutil
import subprocess
from typing import Union

import click
import inquirer
from click import echo
from colorama import Fore, Back

RC_PATH = pathlib.Path("~/.javaversions").expanduser()


def prompt_java_version():
    installations = JavaExecutable.get_known_java_installations()

    if len(installations) == 0:
        echo(f"{Fore.RED}There are no registered Java installations")
        raise click.exceptions.Exit(code=1)

    if len(installations) == 1:
        echo(f"{Fore.YELLOW}Nothing changed, there is only one registered Java version ({installations[0]})")
        return

    options = [(f"{j.version} ({j.path})", j.path) for j in installations]

    answer = inquirer.prompt([inquirer.List("java_ver", message="Which Java version should be used?", choices=options)])

    if not answer:
        raise click.exceptions.Exit(code=1)

    return answer["java_ver"]


class JavaExecutable:
    @classmethod
    def get_known_java_installations(cls, return_paths: bool = False) -> list[Union["JavaExecutable", str]]:
        if not RC_PATH.is_file():
            return []

        with RC_PATH.open("r") as f:
            map_func = str.strip if return_paths else cls
            return list(map(map_func, f.readlines()))

    @classmethod
    def get_default_version(cls) -> "JavaExecutable":
        installs = cls.get_known_java_installations(True)

        if len(installs) == 0:
            print(f"{Fore.RED}No registered java versions. Set the default version using"
                  f"{Fore.WHITE}{Back.BLUE}mcsrv java set")
            raise click.exceptions.Exit(code=1)

        return JavaExecutable(installs[0])

    def __init__(self, path: str):
        self.path: str = path.strip()
        self.version: str = self.get_version()

    def get_version(self) -> str:
        path = shutil.which(self.path)
        if not path:
            echo(f"{Fore.RED}File {self.path!r} is not a valid java installation")
            raise ValueError(f"file {self.path!r} is not a valid java installation")

        self.path = path

        version = subprocess.getoutput(shlex.join([self.path, "--version"])).split("\n")[0]

        if not version.startswith("Unrecognized option: --version"):
            return version

        return subprocess.getoutput(shlex.join([self.path, "-version"])).split("\n")[0]

    def register(self):
        # check if already registered

        javas = self.get_known_java_installations()

        for java in javas:
            if os.path.samefile(java.path, self.path):
                return self

        with RC_PATH.open("a" if RC_PATH.is_file() else "w") as f:
            f.write(f"{self.path}\n")

        return self

    def __str__(self):
        return f"Java Version {self.version!r} at {self.path!r}"

    def __repr__(self):
        return f"<JavaExecutable version={self.version!r} path={self.path!r}>"
