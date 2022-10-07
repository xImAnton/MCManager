import os.path
import pathlib
import shlex
import shutil
import subprocess

from click import echo
from colorama import Fore

RC_PATH = pathlib.Path("~/.javaversions").expanduser()


class JavaExecutable:
    @classmethod
    def get_known_java_installations(cls) -> list["JavaExecutable"]:
        if not RC_PATH.is_file():
            return []

        with RC_PATH.open("r") as f:
            return list(map(cls, f.readlines()))

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
