import pathlib
import re
import shutil
import subprocess
import time
from functools import cached_property
from typing import Optional

import click.exceptions
import colorama
import psutil
from click import echo
from colorama import Fore, Back

from .javaexecutable import JavaExecutable
from .launch import LaunchMethod, LaunchMethodManager
from .properties import ServerProperties
from .util import get_running_screens, Screen, clean_path, check_ram_argument, print_warning, format_bool_indicator

RC_PATH = pathlib.Path("~/.mcsrv").expanduser()
ALL_LIST_PROPERTIES = "ripatxojm"
PLAYER_COUNT_REGEX = re.compile(r"\[.*\][^0-9]+([0-9]+)")


class Server:
    @classmethod
    def get_cached_server_paths(cls) -> list[str]:
        if not RC_PATH.is_file():
            return []

        with RC_PATH.open("r") as f:
            return list(map(str.strip, f.readlines()))

    @classmethod
    def unregister_paths(cls, paths: list[str]) -> None:
        if len(paths) == 0:
            return

        registered = set(cls.get_cached_server_paths())
        to_remove = set(paths)

        with RC_PATH.open("w") as f:
            for valid_server in registered - to_remove:
                f.write(f"{valid_server}\n")

    @classmethod
    def get_registered_servers(cls) -> list["Server"]:
        paths = cls.get_cached_server_paths()
        out = []
        invalid = []

        for p in paths:
            try:
                out.append(Server(p))
            except FileNotFoundError:
                echo(f"mcsrv: warn: {Fore.YELLOW}Server directory {p} not existing, removing it{Fore.RESET}")
                invalid.append(p)

        cls.unregister_paths(invalid)

        return out

    @classmethod
    def get_by_id(cls, server_id: str):
        for path in cls.get_cached_server_paths():
            if pathlib.Path(path).name == server_id:
                return Server(path)
        return None

    def __init__(self, path: str) -> None:
        self.path: pathlib.Path = clean_path(pathlib.Path(path).absolute())

        if not self.path.is_dir():
            raise FileNotFoundError(f"Invalid server path: {self.path!r}")

        self.data: dict[str, str] = {}

        self._load_data()
        self.launch_method_instance: LaunchMethod = self.ensure_valid_launch_method()
        self.save_data()

    @property
    def running(self) -> bool:
        return self.screen_handle is not None

    @property
    def version(self) -> Optional[tuple[str, str, str]]:
        try:
            return self.data["software"], self.data["major"], self.data["minor"]
        except KeyError:
            return None

    @version.setter
    def version(self, version: tuple[str, str, str]):
        self.data["software"] = version[0]
        self.data["major"] = version[1]
        self.data["minor"] = version[2]
        self.save_data()

    @property
    def java_bin_path(self) -> str:
        if "java-bin" not in self.data or not shutil.which(self.data["java-bin"]):
            ver = JavaExecutable.get_default_version()
            print_warning(f"{Fore.YELLOW}Using default Java Version ({ver.version}). Use {Back.BLUE}"
                          f"{Fore.WHITE}mcsrv java set{Back.RESET}{Fore.YELLOW} to set the version manually{Fore.RESET}",
                          "use_def_java")
            return ver.path

        return self.data["java-bin"]

    @java_bin_path.setter
    def java_bin_path(self, val: str) -> None:
        exe = shutil.which(val)

        if not exe:
            self.print(f"{Fore.RED}Invalid java executable: {val}")
            raise click.exceptions.Exit(code=1)

        self.data["java-bin"] = exe
        self.save_data()

    @property
    def java_executable(self) -> JavaExecutable:
        return JavaExecutable(self.java_bin_path)

    @java_executable.setter
    def java_executable(self, val: JavaExecutable) -> None:
        self.java_bin_path = val.path

    @property
    def autostarts(self) -> bool:
        return self.data.get("autostart") == "true"

    @autostarts.setter
    def autostarts(self, val: bool) -> None:
        self.data["autostart"] = "true" if val else "false"
        self.save_data()

    @property
    def launch_method(self) -> tuple[str, str]:
        return self.data.get("launch-method", None), self.data.get("launch-args", None)

    @launch_method.setter
    def launch_method(self, v: tuple[str, str]) -> None:
        method, args = v
        self.data["launch-method"] = method if method in ["jar", "forge"] else None
        self.data["launch-args"] = args
        self.save_data()

    @cached_property
    def screen_handle(self) -> Optional[Screen]:
        for screen in get_running_screens():
            if screen.name == self.screen_name:
                return screen
        return None

    @cached_property
    def properties(self) -> ServerProperties:
        path = self.path.joinpath("server.properties")

        if not path.is_file():
            path.touch()

        return ServerProperties(path)

    @property
    def id(self) -> str:
        return self.path.name.lower()

    @property
    def datafile(self) -> pathlib.Path:
        return self.path.joinpath(".mcsrvmeta")

    @property
    def screen_name(self) -> str:
        return f"mc-{self.id}"

    @property
    def ram(self) -> str:
        return check_ram_argument(self.data.get("ram", "4G"))

    @ram.setter
    def ram(self, val: str) -> None:
        self.data["ram"] = check_ram_argument(val)
        self.save_data()

    @property
    def player_count(self) -> int:
        if not self.running:
            return 0

        self.screen_handle.send_command("list")
        time.sleep(.05)
        out = self.screen_handle.get_last_stdout_lines()

        for i, content in enumerate(out):
            if not content.endswith("list\n"):
                continue

            m = PLAYER_COUNT_REGEX.match(out[i + 1])

            if not m:
                continue

            return int(m.group(1))

        return 0

    def print(self, msg: str) -> None:
        echo(f"mcsrv: {self.id}: {msg}{colorama.Style.RESET_ALL}")

    def register(self) -> "Server":
        # check if my id is already saved in another path
        servers = self.get_registered_servers()

        for other in servers:
            if other.id == self.id:
                # same server
                if str(other.path) == str(self.path):
                    return self

                # other server with same id
                self.print(
                    f"{Fore.RED}There is already a server with id {self.id!r} at {other.path!r}. Rename this or that directory!")
                raise click.exceptions.Exit(code=1)

        # append server if not
        with RC_PATH.open("a" if RC_PATH.is_file() else "w") as f:
            f.write(f"{self.path}\n")

        return self

    def get_stats(self) -> tuple[float, float]:
        if not self.running:
            return 0, 0

        proc: psutil.Process = psutil.Process(self.screen_handle.pid).children()[0]
        return proc.cpu_percent(interval=2.0), round(proc.memory_info().rss / 1000000000, 2)

    def start(self, ram: str = None) -> None:
        if ram:
            ram = check_ram_argument(ram)
        else:
            ram = self.ram

        if shutil.which(self.java_bin_path) is None:
            self.print(f"{Fore.RED}{self.java_bin_path}: Executable not found")
            raise click.exceptions.Exit(code=1)

        # check if eula exists
        eula = pathlib.Path(self.path, "eula.txt")
        if not eula.is_file():
            with eula.open("w") as f:
                f.write("eula=true")

        # invalidate screen handle which is a cached property
        self.__dict__.pop("screen_handle", None)

        self.print(f"Starting {self.launch_method_instance.METHOD} with {ram}B RAM")
        cmd = ["screen", "-d", "-S", self.screen_name, "-m",
               *self.launch_method_instance.get_command(self.java_bin_path, ram)]
        subprocess.run(cmd, cwd=self.path.absolute())

    def ensure_valid_launch_method(self) -> LaunchMethod:
        method = LaunchMethodManager.get_method(self)

        if method and method.is_valid():
            return method

        method = LaunchMethodManager.find_matching_method(self)

        if not method:
            self.print("no server start method detected")
            raise click.exceptions.Exit(1)

        self.launch_method = method.to_tuple()

        return method

    def open_console(self) -> None:
        self.screen_handle.attach()

    def save_data(self) -> None:
        with self.datafile.open("w") as f:
            for key, val in self.data.items():
                f.write(f"{key}={val}\n")

    def _load_data(self) -> None:
        self.data = {}

        if not self.datafile.is_file():
            self.print(f"{Fore.YELLOW}No .mcsrvmeta file found")
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

    def print_restart_note(self) -> None:
        if not self.running:
            return

        self.print(f"{Fore.YELLOW}note that you must restart the server for changes to take effect{Fore.RESET}")

    def stop(self) -> None:
        self.screen_handle.send_command("stop")

    def get_list_data(self, fmt: str = ALL_LIST_PROPERTIES, plain: bool = False) -> list[str]:
        out = []

        if "r" in fmt:  # Running
            out.append(format_bool_indicator(self.running, plain))

        if "i" in fmt:  # ID
            out.append(self.id)

        if "p" in fmt:  # Path
            out.append(self.path)

        if "a" in fmt:  # Autostart
            out.append(format_bool_indicator(self.autostarts, plain))

        if "t" in fmt:  # Type
            out.append(self.launch_method[0])

        if "x" in fmt:  # Performance
            cpu, ram = self.get_stats()
            out.append(f"{cpu}% {ram}GB")

        if "o" in fmt:  # Port
            out.append(self.properties.get_value("server-port"))

        if "j" in fmt:  # Java
            out.append(self.java_executable.version)

        if "m" in fmt:  # Allocated RAM
            out.append(self.ram)

        return out
