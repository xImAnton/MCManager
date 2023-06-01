import os
import pathlib
import re
import shlex
from typing import Optional

from .launch import LaunchMethod

ARG_RE = re.compile(r"^@(libraries\/net\/minecraftforge\/forge\/(.*)\/unix_args\.txt)$")


class ForgeLaunchMethod(LaunchMethod):
    METHOD = "forge"

    @classmethod
    def could_satisfy(cls, path: pathlib.Path) -> Optional[str]:
        if not path.joinpath("user_jvm_args.txt").is_file():
            return

        run_sh = path.joinpath("run.sh")

        if not run_sh.is_file():
            return

        with run_sh.open("r") as f:
            content = f.readlines()

        java_cmd = list(filter(lambda x: x.strip().startswith("java"), content))

        if not java_cmd:
            return

        arg_path = None

        for arg in shlex.split(java_cmd[0].strip()):
            if match := ARG_RE.match(arg):
                arg_path = match.group(1)

        if not arg_path:
            return

        if not path.joinpath(arg_path).is_file():
            return

        os.remove(path.joinpath("user_jvm_args.txt").absolute())
        os.remove(path.joinpath("run.sh").absolute())

        return arg_path

    def get_command(self, java: str, ram: str):
        return [java, "-Xmx" + ram, f"@{self.args}"]

    def is_valid(self):
        return self.path.joinpath(self.args).is_file()
